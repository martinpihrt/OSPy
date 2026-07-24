import threading
import unittest
from unittest import mock

from tests.test_support import TEST_DATA_DIR  # noqa: F401
from ospy import i18n  # noqa: F401
from ospy import log as log_module


class _LockCheckingOptions(object):
    run_log = True

    def __init__(self, checked_lock):
        self._checked_lock = checked_lock
        self.write_observed_unlocked = False

    @property
    def logged_runs(self):
        return []

    @logged_runs.setter
    def logged_runs(self, unused_value):
        result = []

        def acquire_from_another_thread():
            acquired = self._checked_lock.acquire(timeout=0.5)
            result.append(acquired)
            if acquired:
                self._checked_lock.release()

        worker = threading.Thread(target=acquire_from_another_thread)
        worker.start()
        worker.join(1)
        self.write_observed_unlocked = result == [True]


class LogLockingTests(unittest.TestCase):
    def test_run_log_is_persisted_after_releasing_log_lock(self):
        logger = log_module._Log.__new__(log_module._Log)
        logger._lock = threading.RLock()
        logger._log = {'Run': []}
        checked_options = _LockCheckingOptions(logger._lock)

        with mock.patch.object(
                log_module, 'options', checked_options), \
                mock.patch(
                    'ospy.programs.programs.get', return_value=[]
                ):
            logger._save_logs()
            self.assertTrue(log_module._log_persistence_worker.wait_empty())

        self.assertTrue(checked_options.write_observed_unlocked)


if __name__ == '__main__':
    unittest.main()
