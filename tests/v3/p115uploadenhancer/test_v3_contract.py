import ast
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
PLUGIN = ROOT / "plugins.v3" / "p115uploadenhancer"
SOURCE = (PLUGIN / "__init__.py").read_text(encoding="utf-8")
API_SOURCE = (PLUGIN / "p115_api.py").read_text(encoding="utf-8")


def _tree(path: Path):
    return ast.parse(path.read_text(encoding="utf-8"))


def _class_methods(path: Path, class_name: str) -> set[str]:
    tree = _tree(path)
    cls = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == class_name)
    return {node.name for node in cls.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))}


def test_v3_imports_and_version_are_independent():
    assert "from app.sdk.plugin import _PluginBase" in SOURCE
    assert "from app.sdk.events import eventmanager, Event" in SOURCE
    assert "from app.sdk.logging import logger" in SOURCE
    assert "from app.sdk.services import StorageHelper" in SOURCE
    assert "app.core" not in SOURCE + API_SOURCE
    assert "app.log" not in SOURCE + API_SOURCE
    assert "app.helper" not in SOURCE + API_SOURCE
    assert 'plugin_version = "3.0.1"' in SOURCE


def test_storage_contract_methods_and_module_exports():
    methods = _class_methods(PLUGIN / "__init__.py", "P115UploadEnhancer")
    required = {
        "storage_manage", "storage_oper_selection", "list_files", "any_files",
        "upload_file", "download_file", "delete_file", "rename_file",
        "create_folder", "get_folder", "exists", "get_file_item",
        "get_parent_item", "snapshot_storage", "storage_usage", "clear_cache",
    }
    assert required <= methods
    api_methods = _class_methods(PLUGIN / "p115_api.py", "P115Api")
    assert {"move", "copy"} <= api_methods
    for name in required - {"storage_oper_selection", "storage_manage", "clear_cache"}:
        assert f'"{name}"' in SOURCE


def test_new_p115client_directory_api_is_used():
    assert "from p115client.tool.iterdir import iter_files_skim" in API_SOURCE
    assert "with_path=True" in API_SOURCE


def test_v3_index_and_pyproject_contract():
    index = json.loads((ROOT / "package.v3.json").read_text(encoding="utf-8"))
    entry = index["P115UploadEnhancer"]
    assert entry["version"] == "3.0.1"
    assert "v3.0.1" in entry["history"]
    assert entry["system_version"] == ">=3.0.0"
    assert "p115client==0.0.9.7.2" in (PLUGIN / "pyproject.toml").read_text(encoding="utf-8")


def test_no_secret_literals_or_source_tests_in_plugin_directory():
    assert not list(PLUGIN.glob("test_*.py"))
    forbidden = ("Machine ID", "Authorization: Bearer", "__cf_bm=")
    for path in PLUGIN.rglob("*.py"):
        source = path.read_text(encoding="utf-8")
        assert not any(token in source for token in forbidden), path


def test_lifecycle_and_account_api_contracts_are_declared():
    assert "self.stop_service()" in SOURCE
    assert "self._client = None" in SOURCE
    assert "self._p115_api = None" in SOURCE
    assert "self._account_service = None" in SOURCE
    for endpoint in ("/account_status", "/refresh_account_status", "/clear_cache"):
        assert f'"path": "{endpoint}"' in SOURCE
    assert "response_model" in SOURCE
    assert "Cookie" in SOURCE
    assert "account_status" in SOURCE
