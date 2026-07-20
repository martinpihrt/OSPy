import json
import os
import tempfile
import unittest
from unittest import mock

from tests.test_support import TEST_DATA_DIR  # noqa: F401 - initializes isolation
from ospy import health


class IncidentHistoryTests(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.TemporaryDirectory(prefix="ospy-incidents-")
        self.history_file = os.path.join(self.root.name, "incidents.json")
        with health._lock:
            self.original_file = health.INCIDENT_HISTORY_FILE
            self.original_limit = health.INCIDENT_HISTORY_LIMIT
            self.original_issues = health._issues
            self.original_incidents = health._incidents
            self.original_loaded = health._incident_history_loaded
            health.INCIDENT_HISTORY_FILE = self.history_file
            health.INCIDENT_HISTORY_LIMIT = 200
            health._issues = {}
            health._incidents = []
            health._incident_history_loaded = False

    def tearDown(self):
        with health._lock:
            health.INCIDENT_HISTORY_FILE = self.original_file
            health.INCIDENT_HISTORY_LIMIT = self.original_limit
            health._issues = self.original_issues
            health._incidents = self.original_incidents
            health._incident_history_loaded = self.original_loaded
        self.root.cleanup()

    def test_incident_is_persisted_updated_and_resolved(self):
        health.report_issue(
            "database_write", "Database", "Write failed",
            "OSError: disk full", "Free disk space", "/options",
        )
        health.report_issue(
            "database_write", "Database", "Write still fails",
            "OSError: disk full", "Free disk space", "/options",
        )

        active = health.incident_history("open")
        self.assertEqual(len(active), 1)
        self.assertEqual(active[0]["count"], 2)
        self.assertEqual(active[0]["summary"], "Write still fails")
        self.assertTrue(os.path.isfile(self.history_file))

        self.assertTrue(health.resolve_issue("database_write"))
        resolved = health.incident_history("resolved")
        self.assertEqual(len(resolved), 1)
        self.assertGreater(resolved[0]["resolved"], 0)

        with open(self.history_file, "r", encoding="utf-8") as stored_file:
            stored = json.load(stored_file)
        self.assertEqual(stored["version"], 1)
        self.assertEqual(stored["incidents"][0]["status"], "resolved")

    def test_open_incident_from_previous_process_is_marked_interrupted(self):
        health.report_issue(
            "worker", "Worker", "Worker stopped", "RuntimeError", "Restart"
        )
        with health._lock:
            health._issues = {}
            health._incidents = []
            health._incident_history_loaded = False

        interrupted = health.incident_history("interrupted")

        self.assertEqual(len(interrupted), 1)
        self.assertEqual(interrupted[0]["issue_id"], "worker")
        self.assertGreater(interrupted[0]["resolved"], 0)

    def test_history_is_bounded_and_invalid_file_is_recovered(self):
        health.INCIDENT_HISTORY_LIMIT = 3
        with open(self.history_file, "w", encoding="utf-8") as history_file:
            history_file.write("not-json")

        with self.assertLogs(level="WARNING"):
            self.assertEqual(health.incident_history(), [])

        for index in range(5):
            issue_id = "issue-{}".format(index)
            health.report_issue(issue_id, "Issue", str(index))
            health.resolve_issue(issue_id)

        history = health.incident_history(limit=200)
        self.assertEqual(len(history), 3)
        self.assertEqual(
            {item["issue_id"] for item in history},
            {"issue-2", "issue-3", "issue-4"},
        )

    def test_storage_failure_does_not_hide_active_problem(self):
        with self.assertLogs(level="WARNING"), mock.patch.object(
                health.os, "replace", side_effect=OSError("read only")):
            health.report_issue("storage", "Storage", "History failed")

        self.assertEqual(health.active_issues()[0]["id"], "storage")


if __name__ == "__main__":
    unittest.main()
