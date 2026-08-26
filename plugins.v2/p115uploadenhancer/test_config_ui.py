import ast
import unittest
from pathlib import Path


PLUGIN_SOURCE = Path(__file__).with_name("__init__.py")


class ConfigCookieCheckUiTest(unittest.TestCase):
    """配置页 Cookie 检查按钮的静态契约测试。"""

    @classmethod
    def setUpClass(cls) -> None:
        cls.tree = ast.parse(PLUGIN_SOURCE.read_text(encoding="utf-8"))
        cls.source = PLUGIN_SOURCE.read_text(encoding="utf-8")

    def test_cookie_handler_uses_host_api_and_updates_status(self) -> None:
        """按钮必须调用宿主 API，并更新页面状态模型。"""
        handler = next(
            node.value.value
            for node in ast.walk(self.tree)
            if isinstance(node, ast.Assign)
            and any(
                isinstance(target, ast.Name)
                and target.id == "_COOKIE_CHECK_HANDLER"
                for target in node.targets
            )
            and isinstance(node.value, ast.Constant)
            and isinstance(node.value.value, str)
        )
        self.assertIn("window.MoviePilotAPI.post", handler)
        self.assertIn("refresh_account_status", handler)
        self.assertIn("model.cookie_check_status", handler)
        self.assertIn("model.cookie_check_status_type", handler)
        self.assertIn("model.cookie_checking", handler)

    def test_form_contains_bound_status_alert_and_button(self) -> None:
        """配置页必须把状态字段绑定到 VAlert，并使用 onClick。"""
        self.assertIn('"onClick": _COOKIE_CHECK_HANDLER', self.source)
        self.assertIn('"text": "cookie_check_status"', self.source)
        self.assertIn('"type": "cookie_check_status_type"', self.source)
        self.assertIn('"cookie_check_status": "尚未检查 Cookie"', self.source)


if __name__ == "__main__":
    unittest.main()
