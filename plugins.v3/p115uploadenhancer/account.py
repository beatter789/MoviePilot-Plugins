from typing import Any, Dict, Optional

from p115client import check_response

try:
    from .request_guard import P115RequestGuard, is_method_not_allowed
except ImportError:
    from request_guard import P115RequestGuard, is_method_not_allowed


class P115AccountService:
    """
    115 Cookie 检查和账户状态服务
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
