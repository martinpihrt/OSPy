import subprocess
import unittest
from unittest import mock

from tests.test_support import TEST_DATA_DIR  # noqa: F401 - initializes isolation
from ospy import version


class VersionChannelTests(unittest.TestCase):
    def test_master_and_other_branches_keep_plain_version(self):
        revision = version.old_count + 237
        self.assertEqual(version._format_version(revision, "master"), "3.0.237")
        self.assertEqual(version._format_version(revision, "feature/test"), "3.0.237")
        self.assertEqual(version._format_version(revision, ""), "3.0.237")

    def test_beta_branch_gets_beta_suffix_without_changing_revision(self):
        revision = version.old_count + 238
        self.assertEqual(version._format_version(revision, "beta"), "3.0.238-beta")

    def test_current_branch_reads_symbolic_head(self):
        with mock.patch.object(subprocess, "check_output", return_value=b"beta\n") as output:
            self.assertEqual(version._current_branch(), "beta")
        output.assert_called_once_with(
            ["git", "symbolic-ref", "--quiet", "--short", "HEAD"],
            stderr=subprocess.STDOUT,
        )

    def test_detached_head_or_missing_git_has_no_branch_suffix(self):
        with mock.patch.object(subprocess, "check_output", side_effect=OSError("no git")):
            self.assertEqual(version._current_branch(), "")


if __name__ == "__main__":
    unittest.main()
