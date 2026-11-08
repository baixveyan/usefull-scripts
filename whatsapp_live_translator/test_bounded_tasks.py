import threading
import time
import unittest

from bounded_tasks import BoundedTasks
from translation_service import TranslationClient


class BoundedTaskTests(unittest.TestCase):
    def wait_idle(self, pool):
        deadline = time.monotonic() + 3
        while not pool.idle and time.monotonic() < deadline:
            time.sleep(0.005)
        self.assertTrue(pool.idle)

    def test_capacity_cancel_and_close(self):
        started, release = threading.Event(), threading.Event()
        calls = []
        pool = BoundedTasks(workers=1, capacity=2)
        def first():
            started.set()
            release.wait(3)
            calls.append('running')
        try:
            self.assertTrue(pool.submit(first))
            self.assertTrue(started.wait(2))
            self.assertTrue(pool.submit(lambda: calls.append('queued')))
            self.assertFalse(pool.submit(lambda: calls.append('overflow')))
            pool.cancel_pending()
            self.assertTrue(pool.submit(lambda: calls.append('replacement')))
            pool.close()
            self.assertFalse(pool.submit(lambda: None))
            release.set()
            self.wait_idle(pool)
            self.assertEqual(calls, ['running'])
        finally:
            release.set()
            pool.close()

    def test_worker_error_does_not_leak_capacity(self):
        pool = BoundedTasks(workers=1, capacity=1)
        try:
            def fail():
                raise RuntimeError('synthetic failure')
            self.assertTrue(pool.submit(fail))
            self.wait_idle(pool)
            complete = threading.Event()
            self.assertTrue(pool.submit(complete.set))
            self.assertTrue(complete.wait(2))
            self.wait_idle(pool)
        finally:
            pool.close()

    def test_stale_session_cannot_send_to_new_provider(self):
        calls = []
        client = TranslationClient(opener=lambda *args, **kwargs: calls.append(args))
        client.configure('Google', True)
        old_session = client.session
        client.configure('MyMemory', True)
        with self.assertRaises(RuntimeError):
            client.translate('synthetic', 'zh-CN', 'en', session=old_session)
        self.assertEqual(calls, [])


if __name__ == '__main__':
    unittest.main()
