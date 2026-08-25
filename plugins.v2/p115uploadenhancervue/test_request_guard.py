import unittest
from time import monotonic

from request_guard import P115RequestGuard, is_method_not_allowed


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


if __name__ == "__main__":
    unittest.main()
