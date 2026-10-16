import threading
import time
import importlib.util
from pathlib import Path
from unittest.mock import patch

_path = Path(__file__).parents[3] / "plugins.v3" / "p115uploadenhancer" / "tools.py"
_spec = importlib.util.spec_from_file_location("p115uploadenhancer_tools", _path)
_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_module)
RateLimiter = _module.RateLimiter


def test_rate_limiter_reads_clock_only_after_lock_wait():
    limiter = RateLimiter(max_calls=1, time_window=0)
    limiter._lock.acquire()
    clock_read = threading.Event()
    completed = threading.Event()
    real_monotonic = time.monotonic

    def read_clock():
        clock_read.set()
        return real_monotonic()

    def run():
        limiter.acquire()
        completed.set()

    with patch.object(_module, "monotonic", side_effect=read_clock):
        thread = threading.Thread(target=run)
        thread.start()
        assert not clock_read.wait(0.03)
        limiter._lock.release()
        assert clock_read.wait(1)
        assert completed.wait(1)
        thread.join()
