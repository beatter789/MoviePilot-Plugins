from base64 import b64encode
from io import BytesIO
from typing import Any, Dict, Optional

from p115client import P115Client, check_response
from qrcode import make as qr_make

try:
    from .request_guard import P115RequestGuard, is_method_not_allowed
except ImportError:
    from request_guard import P115RequestGuard, is_method_not_allowed


class P115AccountService:
    """
    115 登录二维码、Cookie 检查和账户状态服务
    """

    def __init__(self, client: Any, guard: P115RequestGuard):
        """
        初始化账户服务

        :param client (Any): 受共享节流保护的 P115 客户端
        :param guard (P115RequestGuard): 共享请求控制器
        """
        self.client = client
        self.guard = guard
        self._status_cache: Optional[Dict[str, Any]] = None
        self._status_cache_time = 0.0
        self._status_cache_ttl = 3600.0
        self._status_lock = __import__("threading").Lock()

    def clear_status_cache(self) -> None:
        """
        清除账户状态缓存
        """
        with self._status_lock:
            self._status_cache = None
            self._status_cache_time = 0.0

    def get_status(self, force: bool = False) -> Dict[str, Any]:
        """
        获取 Cookie 有效性、账户信息和空间信息

        :param force (bool): 是否忽略缓存强制请求
        :return Dict: 脱敏后的账户状态
        """
        from time import monotonic

        with self._status_lock:
            now = monotonic()
            if (
                not force
                and self._status_cache is not None
                and now - self._status_cache_time < self._status_cache_ttl
            ):
                return self._status_cache
            try:
                user_resp = self.client.user_my_info()
                check_response(user_resp)
                data = user_resp.get("data", {})
                vip = data.get("vip", {})
                face = data.get("face", {})
                user_info = {
                    "name": data.get("uname"),
                    "is_vip": vip.get("is_vip"),
                    "is_forever_vip": vip.get("is_forever"),
                    "vip_expire_date": (
                        "永久" if vip.get("is_forever") else vip.get("expire_str")
                    ),
                    "avatar": face.get("face_s"),
                }
                space_resp = self.client.fs_index_info(0)
                check_response(space_resp)
                space = space_resp.get("data", {}).get("space_info", {})
                storage_info = {
                    "total": space.get("all_total", {}).get("size_format"),
                    "used": space.get("all_use", {}).get("size_format"),
                    "remaining": space.get("all_remain", {}).get("size_format"),
                }
                result = {
                    "success": True,
                    "cookie_valid": True,
                    "error_message": None,
                    "user_info": user_info,
                    "storage_info": storage_info,
                }
            except Exception as error:
                result = {
                    "success": False,
                    "cookie_valid": False,
                    "error_message": "请在配置页面中设置有效的115网盘Cookie",
                    "user_info": None,
                    "storage_info": None,
                    "detail": str(error),
                }
            self._status_cache = result
            self._status_cache_time = monotonic()
            self._status_cache_ttl = 3600.0 if result.get("success") else 300.0
            return result

    def get_qrcode(self) -> Dict[str, Any]:
        """
        获取 115 登录二维码

        :return Dict: 二维码参数和图片
        """
        self.guard.before_request()
        try:
            response = P115Client.login_qrcode_token()
            check_response(response)
        except Exception as error:
            if is_method_not_allowed(error):
                self.guard.record_method_not_allowed()
            raise
        data = response.get("data") or {}
        uid = str(data.get("uid", ""))
        login_time = str(data.get("time", ""))
        sign = str(data.get("sign", ""))
        if not uid or not login_time or not sign:
            raise RuntimeError("二维码参数不完整")
        content = str(data.get("qrcode") or f"https://115.com/scan/dg-{uid}")
        image = qr_make(content)
        buffer = BytesIO()
        image.save(buffer, format="PNG")
        return {
            "uid": uid,
            "time": login_time,
            "sign": sign,
            "client_type": "alipaymini",
            "qrcode": "data:image/png;base64," + b64encode(buffer.getvalue()).decode(),
            "msg": "请使用115客户端扫描二维码登录",
        }

    def check_qrcode(
        self, uid: str, login_time: str, sign: str, client_type: str = "alipaymini"
    ) -> Dict[str, Any]:
        """
        检查二维码状态并获取登录 Cookie

        :param uid (str): 二维码用户 ID
        :param login_time (str): 二维码时间参数
        :param sign (str): 二维码签名
        :param client_type (str): 登录客户端类型
        :return Dict: 二维码状态，成功时包含 Cookie
        """
        self.guard.before_request()
        try:
            response = P115Client.login_qrcode_scan_status(
                {"uid": uid, "time": login_time, "sign": sign}
            )
            check_response(response)
        except Exception as error:
            if is_method_not_allowed(error):
                self.guard.record_method_not_allowed()
            raise
        status = (response.get("data") or {}).get("status")
        if status == 0 or status is None:
            return {"status": "waiting", "msg": "等待扫码"}
        if status == 1:
            return {"status": "scanned", "msg": "已扫码，等待确认"}
        if status == -1 or status == -2:
            return {"status": "expired", "msg": "二维码已过期或用户取消登录"}
        if status != 2:
            return {"status": "error", "msg": f"未知二维码状态：{status}"}
        self.guard.before_request()
        try:
            result = P115Client.login_qrcode_scan_result(uid, app=client_type)
            check_response(result)
        except Exception as error:
            if is_method_not_allowed(error):
                self.guard.record_method_not_allowed()
            raise
        cookie_data = result.get("data", {}).get("cookie", {})
        cookie = "; ".join(
            f"{name}={value}" for name, value in cookie_data.items() if name and value
        )
        if not cookie:
            return {"status": "error", "msg": "登录成功但未能解析 Cookie"}
        self.clear_status_cache()
        return {"status": "success", "msg": "登录成功", "cookie": cookie}
