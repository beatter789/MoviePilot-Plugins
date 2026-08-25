from threading import Lock
from time import monotonic, sleep
from typing import Any, Callable


class GuardedP115Client:
    """
    为 P115Client 的请求方法增加共享节流和 405 熔断
    """

    def __init__(self, client: Any, guard: "P115RequestGuard"):
        """
        初始化受保护客户端

        :param client (Any): 原始 P115Client

        :param guard (P115RequestGuard): 请求控制器
        """
        self._client = client
        self._guard = guard

    def __getattr__(self, name: str) -> Any:
        """
        获取原始客户端属性并包装可调用请求

        :param name (str): 属性名称

        :return Any: 客户端属性或受保护方法
        """
        target = getattr(self._client, name)
        if not callable(target):
            return target

        def guarded_call(*args: Any, **kwargs: Any) -> Any:
            self._guard.before_request()
            try:
                return target(*args, **kwargs)
            except Exception as error:
                if is_method_not_allowed(error):
                    self._guard.record_method_not_allowed()
                raise

        return guarded_call


class P115RequestGuard:
    """
    115 请求共享节流和错误熔断控制器
    """

    def __init__(self, interval: float = 1.0, circuit_seconds: float = 600.0):
        """
        初始化请求控制器

        :param interval (float): 两次 115 请求之间的最小间隔

        :param circuit_seconds (float): 405 错误后的熔断时间
        """
        self.interval = max(float(interval), 0.0)
        self.circuit_seconds = max(float(circuit_seconds), 0.0)
        self._lock = Lock()
        self._next_request = 0.0
        self._circuit_until = 0.0

    def before_request(self) -> None:
        """
        等待共享请求许可，熔断期间拒绝请求

        :raises RuntimeError: 115 API 处于 405 冷却熔断期间
        """
        while True:
            with self._lock:
                now = monotonic()
                if now < self._circuit_until:
                    remaining = self._circuit_until - now
                    raise RuntimeError(
                        f"115 API 405 冷却中，请等待约 {int(remaining) + 1} 秒"
                    )
                wait_seconds = self._next_request - now
                if wait_seconds <= 0:
                    self._next_request = now + self.interval
                    return
            sleep(wait_seconds)

    def record_method_not_allowed(self) -> None:
        """
        记录 405 并开启请求熔断
        """
        with self._lock:
            self._circuit_until = monotonic() + self.circuit_seconds
            self._next_request = self._circuit_until

    def circuit_remaining(self) -> float:
        """
        获取当前熔断剩余时间

        :return float: 剩余秒数
        """
        with self._lock:
            return max(self._circuit_until - monotonic(), 0.0)


def is_method_not_allowed(error: BaseException) -> bool:
    """
    判断异常是否为 HTTP 405

    :param error (BaseException): 待判断异常

    :return bool: 是否为 405
    """
    return getattr(error, "code", None) == 405 or "405" in str(error)
