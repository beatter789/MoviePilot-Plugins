import ast
import unittest
from pathlib import Path


PLUGIN_SOURCE = Path(__file__).with_name("p115_api.py")


class P115ClientCompatibilityTest(unittest.TestCase):
    """验证 p115client 目录遍历 API 的新旧兼容适配。"""

    @classmethod
    def setUpClass(cls) -> None:
        cls.source = PLUGIN_SOURCE.read_text(encoding="utf-8")
        cls.tree = ast.parse(cls.source)

    def test_supports_old_and_new_iter_helpers(self) -> None:
        imports = {
            alias.name
            for node in ast.walk(self.tree)
            if isinstance(node, ast.ImportFrom)
            and node.module == "p115client.tool.iterdir"
            for alias in node.names
        }
        self.assertIn("iter_files_with_path_skim", imports)
        self.assertIn("iter_files_skim", imports)
        self.assertIn("except ImportError", self.source)

    def test_new_helper_keeps_path_fields_enabled(self) -> None:
        self.assertIn('kwargs.setdefault("with_path", True)', self.source)
        self.assertIn("return _iter_files_skim(*args, **kwargs)", self.source)


if __name__ == "__main__":
    unittest.main()
