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

    def test_cookie_status_alert_is_next_to_check_button(self) -> None:
        """真实 Cookie 状态条应与检查按钮位于同一首行列。"""
        form_source = self.source[self.source.index("def get_legacy_form") :]
        first_row = form_source.index('"component": "VRow"')
        second_row = form_source.index('"component": "VRow"', first_row + 1)
        action_row = form_source[first_row:second_row]
        self.assertIn('"text": "检查 Cookie"', action_row)
        self.assertIn('"text": "cookie_check_status"', action_row)
        self.assertIn('"type": "cookie_check_status_type"', action_row)
        self.assertEqual(form_source.count('"text": "cookie_check_status"'), 1)

    def test_dynamic_cookie_button_demo_is_frontend_only(self) -> None:
        """底部演示按钮只验证模型绑定，不调用任何后端 API。"""
        handler = next(
            node.value.value
            for node in ast.walk(self.tree)
            if isinstance(node, ast.Assign)
            and any(
                isinstance(target, ast.Name)
                and target.id == "_COOKIE_BUTTON_TEST_HANDLER"
                for target in node.targets
            )
            and isinstance(node.value, ast.Constant)
            and isinstance(node.value.value, str)
        )
        self.assertIn("setTimeout", handler)
        self.assertIn("2000", handler)
        self.assertIn("model.cookie_button_test_text", handler)
        self.assertIn("model.cookie_button_test_color", handler)
        self.assertIn("model.cookie_button_test_running", handler)
        self.assertNotIn("MoviePilotAPI", handler)
        self.assertIn('"text": "cookie_button_test_text"', self.source)
        self.assertIn('"color": "cookie_button_test_color"', self.source)
        self.assertIn('"loading": "cookie_button_test_running"', self.source)
        self.assertIn('"disabled": "cookie_button_test_running"', self.source)
        self.assertIn('"cookie_button_test_text": "测试动态 Cookie 按钮"', self.source)
        self.assertIn('"cookie_button_test_color": "info"', self.source)
        self.assertIn('"cookie_button_test_running": False', self.source)

    def test_config_actions_are_next_to_enable_switch(self) -> None:
        """首个配置行应并列呈现启用开关和两个操作按钮。"""
        form_source = self.source[self.source.index("def get_legacy_form") :]
        first_row = form_source.index('"component": "VRow"')
        second_row = form_source.index('"component": "VRow"', first_row + 1)
        action_row = form_source[first_row:second_row]
        self.assertIn('"label": "启用插件"', action_row)
        self.assertIn('"text": "检查 Cookie"', action_row)
        self.assertIn('"text": "清理缓存"', action_row)
        self.assertIn('"color": "info"', action_row)
        self.assertIn('"props": {"cols": 12, "md": 4}', action_row)
        self.assertNotIn('"color": "secondary"', action_row)

    def test_config_actions_are_not_duplicated(self) -> None:
        """移动按钮后配置页不应残留第二组按钮。"""
        form_source = self.source[self.source.index("def get_legacy_form") :]
        self.assertEqual(form_source.count('"text": "检查 Cookie"'), 1)
        self.assertEqual(form_source.count('"text": "清理缓存"'), 1)
        self.assertIn('plugin/P115UploadEnhancer/clear_cache', form_source)

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
