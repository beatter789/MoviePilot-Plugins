import unittest
from time import monotonic
from unittest.mock import patch

from request_guard import P115RequestGuard, is_method_not_allowed
from tools import RateLimiter


class Http405Error(Exception):
    code = 405


class RequestGuardTest(unittest.TestCase):
    """
    请求节流和 405 熔断测试
    """

    def test_interval(self) -> None:
        """
        测试共享请求间隔
        """
        guard = P115RequestGuard(interval=0.01, circuit_seconds=1)
        guard.before_request()
        started = monotonic()
        guard.before_request()
        self.assertGreaterEqual(monotonic() - started, 0.009)

    def test_circuit(self) -> None:
        """
        测试 405 熔断
        """
        guard = P115RequestGuard(interval=0, circuit_seconds=60)
        guard.record_method_not_allowed()
        with self.assertRaises(RuntimeError):
            guard.before_request()

    def test_405_detection(self) -> None:
        """
        测试 405 异常识别
        """
        self.assertTrue(is_method_not_allowed(Http405Error()))
        self.assertTrue(is_method_not_allowed(Exception("HTTP Error 405")))
        self.assertFalse(is_method_not_allowed(Exception("HTTP Error 401")))


class RateLimiterTest(unittest.TestCase):
    """验证限流时间窗口从获得锁后开始计算。"""

    def test_window_clock_is_read_after_lock_acquisition(self) -> None:
        limiter = RateLimiter(max_calls=1, time_window=1.0)
        clock = [0.0]

        class QueuedLock:
            def __enter__(self):
                # 模拟线程在等待锁期间经过了 10 秒。
                clock[0] = 10.0
                limiter._call_times = [9.5]

            def __exit__(self, *args):
                return False

        limiter._lock = QueuedLock()

        with (
            patch("tools.monotonic", side_effect=lambda: clock[0]),
            patch("tools.sleep", side_effect=lambda seconds: clock.__setitem__(0, clock[0] + seconds)) as sleep,
        ):
            limiter.acquire()

        sleep.assert_called_once_with(0.5)
        self.assertEqual(limiter._call_times, [10.5])


if __name__ == "__main__":
    unittest.main()
