import importlib
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

p115client_stub = types.ModuleType("p115client")
p115client_stub.P115Client = MagicMock()
p115client_stub.check_response = lambda response: response
sys.modules.setdefault("p115client", p115client_stub)

qrcode_stub = types.ModuleType("qrcode")
qrcode_stub.make = lambda content: MagicMock()
sys.modules.setdefault("qrcode", qrcode_stub)

from account import P115AccountService
from request_guard import P115RequestGuard


class AccountServiceTest(unittest.TestCase):
    """
    115账户服务测试
    """

    def test_status_mapping_and_cache(self) -> None:
        """
        测试账户字段转换和成功缓存
        """
        client = MagicMock()
        client.user_my_info.return_value = {
            "state": True,
            "data": {
                "uname": "tester",
                "vip": {"is_vip": True, "is_forever": False, "expire_str": "2030-01-01"},
                "face": {"face_s": "avatar"},
            },
        }
        client.fs_index_info.return_value = {
            "state": True,
            "data": {
                "space_info": {
                    "all_total": {"size_format": "1T"},
                    "all_use": {"size_format": "100G"},
                    "all_remain": {"size_format": "900G"},
                }
            },
        }
        service = P115AccountService(client, P115RequestGuard(interval=0))
        first = service.get_status()
        second = service.get_status()
        self.assertTrue(first["success"])
        self.assertEqual(first["user_info"]["name"], "tester")
        self.assertEqual(second["storage_info"]["remaining"], "900G")
        self.assertEqual(client.user_my_info.call_count, 1)

    def test_invalid_cookie_message(self) -> None:
        """
        测试无效 Cookie 固定提示和短缓存
        """
        client = MagicMock()
        client.user_my_info.side_effect = RuntimeError("unauthorized")
        service = P115AccountService(client, P115RequestGuard(interval=0))
        result = service.get_status()
        self.assertFalse(result["success"])
        self.assertEqual(
            result["error_message"],
            "请在配置页面中设置有效的115网盘Cookie",
        )
        self.assertEqual(service._status_cache_ttl, 300.0)

    def test_qrcode_status_mapping(self) -> None:
        """
        测试二维码等待状态映射
        """
        service = P115AccountService(None, P115RequestGuard(interval=0))
        with patch("account.P115Client.login_qrcode_scan_status") as status_call:
            status_call.return_value = {"state": True, "data": {"status": 0}}
            result = service.check_qrcode("uid", "time", "sign")
        self.assertEqual(result["status"], "waiting")


if __name__ == "__main__":
    unittest.main()
