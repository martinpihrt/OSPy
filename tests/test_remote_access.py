import subprocess
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest import mock

from ospy import remote_access


ROOT = Path(__file__).resolve().parents[1]
BASE_TEMPLATE = ROOT / "ospy" / "templates" / "base.html"
HELPERS = ROOT / "ospy" / "helpers.py"
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

    def test_rejects_non_cloudflare_and_embedded_quick_hostnames(self):
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

    def test_normalizes_strict_managed_public_url(self):
        self.assertEqual(
            "https://ospy.example.com",
            remote_access._normalize_cloudflare_managed_url(
                "  https://OSPy.Example.com/\n"
            ),
        )

        for value in (
            "http://ospy.example.com",
            "https://ospy.example.com/login",
            "https://ospy.example.com?x=1",
            "https://user@ospy.example.com",
            "https://ospy.example.com:8443",
            "javascript:alert(1)",
            "ospy.example.com",
            "",
        ):
            with self.subTest(value=value):
                self.assertEqual(
                    "",
                    remote_access._normalize_cloudflare_managed_url(value),
                )

    def test_managed_marker_is_required_before_systemctl(self):
        with mock.patch.object(remote_access.os.path, "isfile", return_value=False), \
                mock.patch.object(remote_access, "_run_command") as run_command:
            self.assertFalse(remote_access._managed_service_is_active())
        run_command.assert_not_called()

    def test_managed_tunnel_has_priority_over_quick_tunnel(self):
        with mock.patch.object(
                remote_access, "_managed_service_is_active", return_value=True), \
                mock.patch.object(
                    remote_access,
                    "_read_cloudflare_managed_url",
                    return_value="https://ospy.example.com",
                ), \
                mock.patch.object(remote_access, "_quick_service_is_active") as quick_active:
            access = remote_access.get_cloudflare_remote_access(force=True)

        self.assertEqual(
            {"mode": "managed", "url": "https://ospy.example.com"},
            access,
        )
        quick_active.assert_not_called()

    def test_invalid_managed_url_falls_back_to_quick_tunnel(self):
        with mock.patch.object(
                remote_access, "_managed_service_is_active", return_value=True), \
                mock.patch.object(
                    remote_access, "_read_cloudflare_managed_url", return_value=""
                ), \
                mock.patch.object(
                    remote_access, "_quick_service_is_active", return_value=True
                ), \
                mock.patch.object(
                    remote_access,
                    "_read_cloudflare_quick_url",
                    return_value="https://fallback-example.trycloudflare.com",
                ):
            access = remote_access.get_cloudflare_remote_access(force=True)

        self.assertEqual(
            {
                "mode": "quick",
                "url": "https://fallback-example.trycloudflare.com",
            },
            access,
        )

    def test_active_quick_service_returns_url_from_last_fifty_journal_lines(self):
        journal = SimpleNamespace(
            returncode=0,
            stdout="Quick Tunnel: https://three-words-here.trycloudflare.com\n",
        )

        with mock.patch.object(
                remote_access, "_managed_service_is_active", return_value=False), \
                mock.patch.object(
                    remote_access, "_quick_service_is_active", return_value=True
                ), \
                mock.patch.object(
                    remote_access, "_run_command", return_value=journal
                ) as run_command:
            access = remote_access.get_cloudflare_remote_access(force=True)

        self.assertEqual(
            {
                "mode": "quick",
                "url": "https://three-words-here.trycloudflare.com",
            },
            access,
        )
        run_command.assert_called_once_with(
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
        )

    def test_cached_quick_url_is_hidden_immediately_when_service_stops(self):
        with mock.patch.object(
                remote_access, "_managed_service_is_active", return_value=False), \
                mock.patch.object(
                    remote_access,
                    "_quick_service_is_active",
                    side_effect=[True, False],
                ), \
                mock.patch.object(
                    remote_access,
                    "_read_cloudflare_quick_url",
                    return_value="https://temporary-example.trycloudflare.com",
                ):
            self.assertEqual(
                {
                    "mode": "quick",
                    "url": "https://temporary-example.trycloudflare.com",
                },
                remote_access.get_cloudflare_remote_access(force=True),
            )
            self.assertIsNone(remote_access.get_cloudflare_remote_access())

    def test_quick_result_is_cached_for_normal_footer_rendering(self):
        with mock.patch.object(
                remote_access, "_managed_service_is_active", return_value=False), \
                mock.patch.object(
                    remote_access, "_quick_service_is_active", return_value=True
                ), \
                mock.patch.object(
                    remote_access,
                    "_read_cloudflare_quick_url",
                    return_value="https://cached-example.trycloudflare.com",
                ) as read_quick:
            first = remote_access.get_cloudflare_remote_access(force=True)
            second = remote_access.get_cloudflare_remote_access()

        self.assertEqual(first, second)
        read_quick.assert_called_once_with()

    def test_backward_quick_helper_never_returns_managed_url(self):
        with mock.patch.object(
                remote_access,
                "get_cloudflare_remote_access",
                return_value={"mode": "managed", "url": "https://ospy.example.com"},
        ):
            self.assertEqual("", remote_access.get_cloudflare_quick_url(force=True))

        with mock.patch.object(
                remote_access,
                "get_cloudflare_remote_access",
                return_value={
                    "mode": "quick",
                    "url": "https://quick-example.trycloudflare.com",
                },
        ):
            self.assertEqual(
                "https://quick-example.trycloudflare.com",
                remote_access.get_cloudflare_quick_url(force=True),
            )

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

    def test_base_template_shows_managed_or_quick_cloudflare_link(self):
        source = BASE_TEMPLATE.read_text(encoding="utf-8")
        self.assertNotIn("from ospy.remote_access import", source)
        self.assertIn(
            "cloudflare_access = get_cloudflare_remote_access()",
            source,
        )
        self.assertIn("$if cloudflare_access:", source)
        self.assertIn("cloudflare_access['mode'] == 'managed'", source)
        self.assertIn("cloudflare_access['mode'] == 'quick'", source)
        self.assertIn('id="cloudflare_managed"', source)
        self.assertIn('id="cloudflare_quick"', source)
        self.assertIn("$_('Cloudflare Tunnel')", source)
        self.assertIn("$_('Cloudflare Quick Tunnel')", source)
        self.assertIn('href="${cloudflare_access[\'url\']}"', source)
        self.assertIn('target="_blank"', source)
        self.assertIn('rel="noopener noreferrer"', source)

    def test_template_globals_exposes_cloudflare_helpers(self):
        source = HELPERS.read_text(encoding="utf-8")
        self.assertIn("get_cloudflare_quick_url", source)
        self.assertIn("get_cloudflare_remote_access", source)
        self.assertIn("from ospy.remote_access import", source)
        self.assertIn("result.update(locals())", source)

    def test_clean_installation_documents_both_footer_modes(self):
        source = CLEAN_INSTALLATION.read_text(encoding="utf-8")
        self.assertIn("/etc/ospy/cloudflare_public_url", source)
        self.assertIn("clickable **Cloudflare Tunnel** link in the footer", source)
        self.assertIn("clickable **Cloudflare Quick Tunnel** link in the footer", source)
        self.assertIn("display priority over a Quick Tunnel", source)
        self.assertIn("No TLS Verify", source)


if __name__ == "__main__":
    unittest.main()
