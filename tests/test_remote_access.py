import subprocess
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest import mock

from ospy import remote_access


ROOT = Path(__file__).resolve().parents[1]
BASE_TEMPLATE = ROOT / "ospy" / "templates" / "base.html"
CLEAN_INSTALLATION = ROOT / "ospy" / "docs" / "Clean_installation.md"


class RemoteAccessTests(unittest.TestCase):
    def setUp(self):
        remote_access._cache_url = ""
        remote_access._cache_until = 0.0

    def test_extracts_last_strict_quick_tunnel_url(self):
        journal = """
        INF Your quick Tunnel has been created! Visit it at:
        https://first-example.trycloudflare.com
        another line
        https://latest-example.trycloudflare.com
        """
        self.assertEqual(
            "https://latest-example.trycloudflare.com",
            remote_access._extract_cloudflare_quick_url(journal),
        )

    def test_rejects_non_cloudflare_and_embedded_hostnames(self):
        for value in (
            "https://example.com",
            "http://demo.trycloudflare.com",
            "https://demo.trycloudflare.com.evil.example",
            "https://trycloudflare.com",
            "",
        ):
            with self.subTest(value=value):
                self.assertEqual(
                    "",
                    remote_access._extract_cloudflare_quick_url(value),
                )

    def test_missing_service_file_returns_empty_without_running_commands(self):
        with mock.patch.object(remote_access.os.path, "isfile", return_value=False), \
                mock.patch.object(remote_access, "_run_command") as run_command:
            self.assertEqual("", remote_access.get_cloudflare_quick_url(force=True))

        run_command.assert_not_called()

    def test_inactive_service_returns_empty_without_reading_journal(self):
        inactive = SimpleNamespace(returncode=3, stdout="")
        with mock.patch.object(remote_access.os.path, "isfile", return_value=True), \
                mock.patch.object(
                    remote_access, "_run_command", return_value=inactive) as run_command:
            self.assertEqual("", remote_access.get_cloudflare_quick_url(force=True))

        run_command.assert_called_once_with(
            [
                "systemctl",
                "is-active",
                "--quiet",
                "ospy-cloudflared-quick.service",
            ]
        )

    def test_active_service_returns_url_from_last_fifty_journal_lines(self):
        active = SimpleNamespace(returncode=0, stdout="")
        journal = SimpleNamespace(
            returncode=0,
            stdout="Quick Tunnel: https://three-words-here.trycloudflare.com\n",
        )

        with mock.patch.object(remote_access.os.path, "isfile", return_value=True), \
                mock.patch.object(
                    remote_access, "_run_command", side_effect=[active, journal]) as run_command:
            url = remote_access.get_cloudflare_quick_url(force=True)

        self.assertEqual(
            "https://three-words-here.trycloudflare.com",
            url,
        )
        self.assertEqual(
            [
                mock.call(
                    [
                        "systemctl",
                        "is-active",
                        "--quiet",
                        "ospy-cloudflared-quick.service",
                    ]
                ),
                mock.call(
                    [
                        "journalctl",
                        "-u",
                        "ospy-cloudflared-quick.service",
                        "-n",
                        "50",
                        "--no-pager",
                        "-o",
                        "cat",
                    ]
                ),
            ],
            run_command.call_args_list,
        )

    def test_cached_url_is_hidden_immediately_when_service_stops(self):
        active = SimpleNamespace(returncode=0, stdout="")
        inactive = SimpleNamespace(returncode=3, stdout="")
        journal = SimpleNamespace(
            returncode=0,
            stdout="https://temporary-example.trycloudflare.com\n",
        )

        with mock.patch.object(remote_access.os.path, "isfile", return_value=True), \
                mock.patch.object(
                    remote_access,
                    "_run_command",
                    side_effect=[active, journal, inactive],
                ):
            self.assertEqual(
                "https://temporary-example.trycloudflare.com",
                remote_access.get_cloudflare_quick_url(force=True),
            )
            self.assertEqual("", remote_access.get_cloudflare_quick_url())

    def test_command_failure_or_timeout_is_fail_closed(self):
        with mock.patch.object(
                remote_access.subprocess,
                "run",
                side_effect=subprocess.TimeoutExpired("systemctl", 1.5)):
            self.assertIsNone(
                remote_access._run_command(
                    ["systemctl", "is-active", "--quiet", "test.service"]
                )
            )

    def test_result_is_cached_for_normal_footer_rendering(self):
        active = SimpleNamespace(returncode=0, stdout="")
        journal = SimpleNamespace(
            returncode=0,
            stdout="https://cached-example.trycloudflare.com\n",
        )

        with mock.patch.object(remote_access.os.path, "isfile", return_value=True), \
                mock.patch.object(
                    remote_access,
                    "_run_command",
                    side_effect=[active, journal, active],
                ) as run_command:
            first = remote_access.get_cloudflare_quick_url(force=True)
            second = remote_access.get_cloudflare_quick_url()

        self.assertEqual(first, second)
        self.assertEqual(3, run_command.call_count)
        journal_calls = [
            call for call in run_command.call_args_list
            if call.args and call.args[0][0] == "journalctl"
        ]
        self.assertEqual(1, len(journal_calls))

    def test_base_template_shows_only_a_valid_quick_tunnel_result(self):
        source = BASE_TEMPLATE.read_text(encoding="utf-8")
        self.assertIn(
            "from ospy.remote_access import get_cloudflare_quick_url",
            source,
        )
        self.assertIn(
            "cloudflare_quick_url = get_cloudflare_quick_url()",
            source,
        )
        self.assertIn("$if cloudflare_quick_url:", source)
        self.assertIn('id="cloudflare_quick"', source)
        self.assertIn('href="${cloudflare_quick_url}"', source)
        self.assertIn('target="_blank"', source)
        self.assertIn('rel="noopener noreferrer"', source)


    def test_clean_installation_documents_footer_link_behavior(self):
        source = CLEAN_INSTALLATION.read_text(encoding="utf-8")
        self.assertIn("OSPy also shows the current Quick Tunnel address", source)
        self.assertIn("clickable **Cloudflare Quick Tunnel** link in the footer", source)
        self.assertIn("the footer does not show the link", source)



if __name__ == "__main__":
    unittest.main()
