"""Bounded background work with nonblocking submissions and explicit shutdown."""
from concurrent.futures import ThreadPoolExecutor
import threading


class BoundedTasks:
    def __init__(self, workers=2, capacity=10):
        if workers < 1 or capacity < workers:
            raise ValueError('capacity must be >= workers >= 1')
        self._executor = ThreadPoolExecutor(max_workers=workers, thread_name_prefix='translation')
        self._slots = threading.BoundedSemaphore(capacity)
        self._lock = threading.RLock()
        self._futures = set()
        self._closed = False

    def submit(self, callback, *args):
        with self._lock:
            if self._closed or not self._slots.acquire(blocking=False):
                return False
            try:
                future = self._executor.submit(callback, *args)
            except Exception:
                self._slots.release()
                raise
            self._futures.add(future)
            future.add_done_callback(self._finished)
            return True

    def _finished(self, future):
        with self._lock:
            self._futures.discard(future)
            self._slots.release()

    def cancel_pending(self):
        with self._lock:
            for future in tuple(self._futures):
                future.cancel()

    @property
    def idle(self):
        with self._lock:
            return not self._futures

    def close(self):
        with self._lock:
            self._closed = True
            self._executor.shutdown(wait=False, cancel_futures=True)
