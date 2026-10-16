import importlib.util
import sys
import types
from pathlib import Path


def test_plugin_imports_with_v3_sdk_contract_stubs(monkeypatch):
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
    add("app.sdk")
    add("app.sdk.events", eventmanager=EventManager(), Event=type("Event", (), {}))
    add("app.sdk.logging", logger=types.SimpleNamespace(
        info=lambda *args, **kwargs: None,
        warning=lambda *args, **kwargs: None,
        warn=lambda *args, **kwargs: None,
        error=lambda *args, **kwargs: None,
        debug=lambda *args, **kwargs: None,
    ))
    add("app.sdk.plugin", _PluginBase=type("_PluginBase", (), {"__init__": lambda self: None}))
    add("app.sdk.services", StorageHelper=type("StorageHelper", (), {}))
    add("app.sdk.config", settings=types.SimpleNamespace(), global_vars={})
    add("app.sdk.cache", TTLCache=type("TTLCache", (), {
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

    root = Path(__file__).resolve().parents[3] / "plugins.v3" / "p115uploadenhancer"
    spec = importlib.util.spec_from_file_location(
        "v3_p115uploadenhancer_test_import",
        root / "__init__.py",
        submodule_search_locations=[str(root)],
    )
    module = importlib.util.module_from_spec(spec)
    monkeypatch.setitem(sys.modules, spec.name, module)
    spec.loader.exec_module(module)
    plugin = module.P115UploadEnhancer()
    assert plugin.plugin_version == "3.0.1"
    assert "storage_manage" in plugin.get_module()
    status = plugin.account_status()
    assert status.success is False
    assert status.data["cookie_valid"] is False
