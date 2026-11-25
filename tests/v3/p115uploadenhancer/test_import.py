import importlib.util
import sys
import types
from hashlib import sha1
from pathlib import Path
from unittest.mock import MagicMock, Mock

import pytest
from p115client import P115Client
from p115client.type import P115URL


@pytest.fixture(params=[("v2", "1.1.13"), ("v3", "3.0.3")], ids=["v2", "v3"])
def plugin_module(monkeypatch, request):
    generation, version = request.param
    class EventManager:
        def register(self, *args, **kwargs):
            return lambda function: function

    class Response:
        def __init__(self, success=True, message="", data=None):
            self.success, self.message, self.data = success, message, data

    def add(name, **attrs):
        module = types.ModuleType(name)
        for key, value in attrs.items():
            setattr(module, key, value)
        monkeypatch.setitem(sys.modules, name, module)

    add("app")
    is_v3 = generation == "v3"
    prefix = "app.sdk" if is_v3 else "app.core"
    add(prefix)
    if not is_v3:
        add("app.helper")
    event_module = "events" if is_v3 else "event"
    add(f"{prefix}.{event_module}", eventmanager=EventManager(), Event=type("Event", (), {}))
    add("app.sdk.logging" if is_v3 else "app.log", logger=Mock())
    add("app.sdk.plugin" if is_v3 else "app.plugins", _PluginBase=type("_PluginBase", (), {}))
    add("app.sdk.services" if is_v3 else "app.helper.storage", StorageHelper=type("StorageHelper", (), {}))
    add(f"{prefix}.config", settings=types.SimpleNamespace(USER_AGENT="default-agent"),
        global_vars=types.SimpleNamespace(is_transfer_stopped=lambda _: False))
    add(f"{prefix}.cache", TTLCache=type("TTLCache", (), {
        "__init__": lambda self, *args, **kwargs: None,
        "get": lambda self, *args: None,
        "set": lambda self, *args: None,
        "clear": lambda self: None,
    }))
    add("app.schemas", Response=Response,
        StorageOperSelectionEventData=type("StorageOperSelectionEventData", (), {}),
        FileItem=type("FileItem", (), {}), StorageUsage=type("StorageUsage", (), {}))
    add("app.schemas.types", ChainEventType=types.SimpleNamespace(StorageOperSelection="StorageOperSelection"))
    add("app.schemas.exception", StorageQueryError=type("StorageQueryError", (Exception,), {}))
    add("app.modules")
    add("app.modules.filemanager")
    add("app.modules.filemanager.storages", transfer_process=lambda *args, **kwargs: None)

    root = Path(__file__).resolve().parents[3] / f"plugins.{generation}" / "p115uploadenhancer"
    spec = importlib.util.spec_from_file_location(
        f"{generation}_p115uploadenhancer_test_import",
        root / "__init__.py",
        submodule_search_locations=[str(root)],
    )
    module = importlib.util.module_from_spec(spec)
    monkeypatch.setitem(sys.modules, spec.name, module)
    spec.loader.exec_module(module)
    return module, version


def test_plugin_imports_with_host_contract_stubs(plugin_module):
    module, version = plugin_module
    plugin = module.P115UploadEnhancer()
    assert plugin.plugin_version == version
    assert "upload_file" in plugin.get_module()
    status = plugin.account_status()
    if version.startswith("3."):
        assert "storage_manage" in plugin.get_module()
        assert status.success is False
        assert status.data["cookie_valid"] is False
    else:
        assert status["success"] is False
        assert status["cookie_valid"] is False


@pytest.fixture
def api(plugin_module, monkeypatch):
    module, _ = plugin_module
    client = module.create_client(
        "UID=1_A1_1; CID=example; SEID=example",
        default_timeout={"connect": 3, "read": 10},
    )
    api = module.P115Api(client, "test")
    api._request_guard.interval = 0
    api_module = sys.modules[module.P115Api.__module__]
    monkeypatch.setattr(api_module, "transfer_process", Mock(return_value=Mock()))
    return api_module, api


@pytest.mark.parametrize("response_cid", [42, 0])
def test_cookie_directory_api_and_invalid_cache(api, monkeypatch, response_cid):
    _, instance = api
    web = Mock(return_value={"state": True, "cid": response_cid, "count": 0, "offset": 0, "data": []})
    open_api = Mock(side_effect=AssertionError("unexpected Open API"))
    monkeypatch.setattr(P115Client, "fs_files", web)
    monkeypatch.setattr(P115Client, "fs_files_open", open_api)
    instance._id_cache = Mock()
    instance._id_item_cache = Mock()

    assert instance.list(types.SimpleNamespace(path="/folder/", type="dir", fileid="42")) == []
    web.assert_called_once()
    open_api.assert_not_called()
    for cache in (instance._id_cache, instance._id_item_cache):
        if response_cid == 42:
            cache.remove.assert_not_called()
        else:
            cache.remove.assert_called_once_with(id=42)


def test_download_forwards_sdk_headers(api, monkeypatch, tmp_path):
    module, instance = api
    url = "https://example.invalid/file"
    get_url = Mock(return_value=P115URL(url, headers={"User-Agent": "bound-agent", "Cookie": "session=example"}))
    monkeypatch.setattr(P115Client, "download_url", get_url)
    response = Mock()
    response.iter_bytes.return_value = [b"data"]
    stream = MagicMock()
    stream.return_value.__enter__.return_value = response
    monkeypatch.setattr(module, "stream", stream)
    instance.get_item = Mock(return_value=types.SimpleNamespace(pickcode="pick", size=4))

    path = instance.download(types.SimpleNamespace(path="/file", name="file"), tmp_path)
    assert path.read_bytes() == b"data"
    get_url.assert_called_once()
    stream.assert_called_once_with("GET", url, headers={"user-agent": "bound-agent", "cookie": "session=example"})


@pytest.mark.parametrize("statuses", [(7, 2), (1, 2), (1, 1, 2), (1, 1, 1)])
def test_upload_reuse_and_oss_fallback(api, monkeypatch, tmp_path, statuses):
    module, instance = api
    content = b"abcdef"
    local = tmp_path / "local.bin"
    local.write_bytes(content)
    directory = types.SimpleNamespace(path="/target", fileid="42")
    instance.get_folder = Mock(return_value=directory)
    uploaded = object()
    instance.get_item = Mock(return_value=uploaded)
    instance.upload_config.update(upload_module_wait_time=1, upload_module_wait_timeout=1)
    current_time = [0]
    monkeypatch.setattr(module, "perf_counter", lambda: current_time[0])

    def sleep(seconds):
        current_time[0] += seconds

    monkeypatch.setattr(module, "sleep", sleep)
    oss_payload = {"bucket": "test-bucket", "object": "key", "callback": {"callback": "a", "callback_var": "b"}}
    replies = {
        1: {"status": 1, **oss_payload},
        2: {"status": 2},
        7: {"status": 7, "sign_key": "challenge", "sign_check": "1-3"},
    }
    requests = []
    pending = iter(statuses)

    def upload_init(self, payload, **kwargs):
        requests.append((dict(payload), kwargs))
        return replies[next(pending)].copy()

    monkeypatch.setattr(P115Client, "upload_init", upload_init)
    token = Mock(return_value={
        "state": True, "AccessKeyId": "id", "AccessKeySecret": "secret",
        "SecurityToken": "test-token", "Expiration": "2099-01-01T00:00:00Z",
    })
    monkeypatch.setattr(P115Client, "upload_gettoken", staticmethod(token))
    bucket = Mock()
    bucket.complete_multipart_upload.return_value.status = 200
    monkeypatch.setattr(module, "Bucket", Mock(return_value=bucket))

    assert instance.upload(directory, local, "remote.bin") is uploaded
    instance.get_item.assert_called_once_with(Path("/target/remote.bin"))
    assert len(requests) == len(statuses)
    for payload, kwargs in requests:
        assert payload["target"] == "U_1_42"
        assert payload["fileid"] == sha1(content).hexdigest().upper()
        assert payload["filename"] == "remote.bin"
        assert "timeout" in kwargs
    if statuses[0] == 7:
        assert requests[1][0]["sign_val"] == sha1(content[1:4]).hexdigest().upper()
    if statuses[-1] == 2:
        token.assert_not_called()
        bucket.init_multipart_upload.assert_not_called()
    else:
        token.assert_called_once()
        bucket.init_multipart_upload.assert_called_once()
        bucket.upload_part.assert_called_once()
        bucket.complete_multipart_upload.assert_called_once()
