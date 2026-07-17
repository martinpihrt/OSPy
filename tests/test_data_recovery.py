import datetime
import unittest

from tests.test_support import TEST_DATA_DIR  # noqa: F401 - initializes isolation
from ospy import i18n  # noqa: F401 - installs gettext
from ospy import log as log_module


class PersistedLogRecoveryTests(unittest.TestCase):
    def test_invalid_run_records_are_discarded(self):
        valid = {
            "time": datetime.datetime(2030, 1, 1, 10, 0),
            "level": 20,
            "data": {
                "uid": "run-1",
                "start": datetime.datetime(2030, 1, 1, 10, 0),
                "end": datetime.datetime(2030, 1, 1, 10, 5),
                "station": 0,
                "active": False,
            },
        }

        with self.assertLogs(level="WARNING"):
            cleaned = log_module._clean_records(
                [valid, "invalid", {"time": "invalid"}],
                log_module._valid_run_record,
                "run",
            )

        self.assertEqual(cleaned, [valid])

    def test_invalid_event_record_does_not_reach_rendering(self):
        self.assertIsNone(log_module.normalize_event_record("invalid"))

    def test_invalid_text_log_records_are_discarded(self):
        valid = {
            "time": "10:00:00",
            "date": "2030-01-01",
            "subject": "Subject",
            "status": "Sent",
        }
        validator = lambda entry: log_module._valid_text_record(
            entry, ("time", "date", "subject", "status")
        )

        with self.assertLogs(level="WARNING"):
            cleaned = log_module._clean_records(
                [valid, {"time": 10}, None], validator, "text"
            )

        self.assertEqual(cleaned, [valid])


if __name__ == "__main__":
    unittest.main()
