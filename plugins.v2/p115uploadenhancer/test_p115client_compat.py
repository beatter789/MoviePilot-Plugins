import ast
import unittest
from pathlib import Path


PLUGIN_SOURCE = Path(__file__).with_name("p115_api.py")
REQUIREMENTS = PLUGIN_SOURCE.with_name("requirements.txt")


class P115ClientCompatibilityTest(unittest.TestCase):
    """验证固定版本 SDK 的目录遍历兼容性。"""

    @classmethod
    def setUpClass(cls) -> None:
        cls.source = PLUGIN_SOURCE.read_text(encoding="utf-8")
        cls.tree = ast.parse(cls.source)

    def test_directory_helper_keeps_path_fields_enabled(self) -> None:
        calls = [
            node for node in ast.walk(self.tree)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "iter_files_skim"
        ]
        self.assertTrue(calls)
        for call in calls:
            options = {kw.arg: kw.value for kw in call.keywords}
            self.assertIs(ast.literal_eval(options["with_path"]), True)

    def test_requirements_pin_target_release(self) -> None:
        requirements = REQUIREMENTS.read_text(encoding="utf-8").splitlines()
        self.assertEqual(
            [line for line in requirements if line.startswith("p115client")],
            ["p115client==0.0.9.7.8.3"],
        )


if __name__ == "__main__":
    unittest.main()
