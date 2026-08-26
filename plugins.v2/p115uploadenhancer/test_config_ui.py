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

    def test_account_page_uses_eight_responsive_cards(self) -> None:
        """账户主页必须保留八张响应式卡片及统一的 VCard 结构。"""
        for label in (
            "115账户信息",
            "Cookie",
            "用户名",
            "VIP",
            "VIP到期",
            "总空间",
            "已用空间",
            "剩余空间",
        ):
            self.assertIn(f'"{label}"', self.source)
        self.assertIn("def _build_account_card", self.source)
        self.assertIn('"component": "VCard"', self.source)
        self.assertIn('"component": "VCardText"', self.source)
        self.assertIn('"variant": "tonal"', self.source)
        self.assertIn('"color": color', self.source)
        self.assertIn('"props": {"cols": 12, "sm": 6, "md": 3}', self.source)
        self.assertIn('account_text, cookie_text = "账户状态正常", "有效"', self.source)
        self.assertIn('account_text, cookie_text = "账户状态异常", "无效"', self.source)

    def test_account_page_keeps_refresh_endpoint_and_safe_failure_notice(self) -> None:
        """刷新按钮和失败提示必须存在，且提示不包含敏感字段。"""
        self.assertIn("plugin/P115UploadEnhancer/refresh_account_status", self.source)
        self.assertIn("账户信息获取失败，请检查 Cookie 配置后重试。", self.source)
        self.assertNotIn('"detail"', self.source[self.source.index("def get_page"):])


if __name__ == "__main__":
    unittest.main()
