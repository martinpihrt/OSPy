import os
from pathlib import Path
import shutil
import subprocess
import unittest


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INSTALLER = os.path.join(ROOT, "ospy_setup.sh")
SERVICE = os.path.join(ROOT, "service", "ospy.service")
CLEAN_GUIDE = os.path.join(ROOT, "ospy", "docs", "Clean_installation.md")


class CleanInstallationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open(INSTALLER, "r", encoding="utf-8") as source:
            cls.installer = source.read()
        with open(SERVICE, "r", encoding="utf-8") as source:
            cls.service = source.read()
        with open(CLEAN_GUIDE, "r", encoding="utf-8") as source:
            cls.clean_guide = source.read()

    def test_installer_has_valid_bash_syntax(self):
        if os.name == "nt":
            self.skipTest("POSIX shell required")
        bash = shutil.which("bash")
        if not bash:
            self.skipTest("bash is not available")
        result = subprocess.run(
            [bash, "-n", INSTALLER],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=15,
        )
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_installer_fails_safely_and_uses_stable_checkout(self):
        self.assertTrue(self.installer.startswith("#!/bin/bash\nset -Eeuo pipefail"))
        self.assertIn("trap 'echo \"OSPy installation failed", self.installer)
        self.assertIn("git clone --branch master --single-branch", self.installer)
        self.assertIn("An existing OSPy checkout was found and left unchanged.", self.installer)
        self.assertNotIn("reset --hard", self.installer)
        self.assertNotIn("rm -rf", self.installer)

    def test_installer_does_not_execute_unverified_dependency_archives(self):
        for unsafe_fragment in (
                "files.pythonhosted.org", "log2ram", "mysql-connector-python",
                "tar xf", "./install.sh"):
            with self.subTest(fragment=unsafe_fragment):
                self.assertNotIn(unsafe_fragment, self.installer)
        self.assertIn("python3-cmarkgfm", self.installer)
        self.assertIn("python3-qrcode", self.installer)
        self.assertIn('"5" "Install multimedia packages for voice plug-ins" OFF', self.installer)

    def test_installer_verifies_builtin_sqlite_support_in_memory(self):
        self.assertIn("import sqlite3", self.installer)
        self.assertIn("sqlite3.connect(':memory:')", self.installer)
        self.assertIn("PRAGMA integrity_check", self.installer)
        self.assertNotIn("sqlite3.db", self.installer)
        self.assertNotIn("pip install sqlite", self.installer.lower())

    def test_installer_uses_and_validates_the_versioned_service_template(self):
        self.assertIn('service_template="$ospy_dir/service/ospy.service"', self.installer)
        self.assertIn('s|{{OSPY_DIR}}|$ospy_dir|g', self.installer)
        self.assertIn('s|{{PYTHON}}|$python_path|g', self.installer)
        self.assertIn("systemctl daemon-reload", self.installer)
        self.assertIn("systemctl restart ospy.service", self.installer)
        self.assertIn("systemctl is-active --quiet ospy.service", self.installer)
        self.assertIn("journalctl -u ospy.service", self.installer)

    def test_native_service_has_bounded_recovery_and_no_unresolved_runtime_paths(self):
        self.assertIn("WorkingDirectory={{OSPY_DIR}}", self.service)
        self.assertIn("ExecStart={{PYTHON}} -u {{OSPY_DIR}}/run.py", self.service)
        self.assertIn("Restart=on-failure", self.service)
        self.assertIn("RestartSec=5", self.service)
        self.assertIn("TimeoutStopSec=45", self.service)
        self.assertIn("KillMode=control-group", self.service)
        rendered = self.service.replace("{{OSPY_DIR}}", "/opt/OSPy").replace(
            "{{PYTHON}}", "/usr/bin/python3"
        )
        self.assertNotIn("{{", rendered)
        self.assertNotIn("}}", rendered)

    def test_installer_offers_all_remote_access_modes(self):
        expected_modes = (
            '"lan"',
            '"cloudflare"',
            '"cloudflare-quick"',
            '"tailscale-serve"',
            '"tailscale-funnel"',
        )
        for mode in expected_modes:
            with self.subTest(mode=mode):
                self.assertIn(mode, self.installer)

        self.assertIn("OSPy remote access - explanation", self.installer)
        self.assertIn("Local network only", self.installer)
        self.assertIn("Cloudflare Tunnel", self.installer)
        self.assertIn("Cloudflare Quick Tunnel", self.installer)
        self.assertIn("Tailscale Serve", self.installer)
        self.assertIn("Tailscale Funnel", self.installer)

    def test_remote_access_keeps_cloudflare_origin_on_loopback(self):
        self.assertIn("http://127.0.0.1:8080", self.installer)
        self.assertIn("https://127.0.0.1:8080", self.installer)
        self.assertIn("http://<Raspberry-Pi-IP>:8080", self.installer)
        self.assertIn("detect_ospy_origin()", self.installer)

        # Cloudflare must reach only the local OSPy origin; the installer never opens port 8080.
        self.assertNotIn("certbot certonly", self.installer)
        self.assertNotIn("openssl req", self.installer)
        self.assertNotIn("ufw allow 8080", self.installer)
        self.assertNotIn("iptables -A INPUT", self.installer)

    def test_cloudflare_managed_tunnel_is_installed_safely(self):
        self.assertIn("https://pkg.cloudflare.com/cloudflare-main.gpg", self.installer)
        self.assertIn("https://pkg.cloudflare.com/cloudflared", self.installer)
        self.assertIn("apt-get install -y cloudflared", self.installer)

        self.assertIn('cloudflare_token=""', self.installer)
        self.assertIn('cloudflare_hostname=""', self.installer)
        self.assertIn('cloudflare_public_url_file="/etc/ospy/cloudflare_public_url"', self.installer)
        self.assertIn("Cloudflare public hostname", self.installer)
        self.assertIn("normalize_cloudflare_hostname", self.installer)
        self.assertIn("a Tunnel token is not required for this run", self.installer)
        self.assertIn("--passwordbox", self.installer)
        self.assertIn('cloudflared service install "$cloudflare_token"', self.installer)
        self.assertIn("systemctl restart cloudflared.service", self.installer)
        self.assertIn("systemctl is-active --quiet cloudflared.service", self.installer)
        self.assertIn('remote_url="https://$cloudflare_hostname"', self.installer)
        self.assertIn("printf '%s\\n' \"$remote_url\" > \"$cloudflare_public_url_file\"", self.installer)
        self.assertIn("No TLS Verify", self.installer)

        # The token must not be printed back to the terminal or written to a project file.
        self.assertNotIn('echo "$cloudflare_token"', self.installer)
        self.assertNotIn('printf "%s" "$cloudflare_token"', self.installer)
        self.assertNotIn('> "$ospy_dir/cloudflare_token"', self.installer)
        self.assertNotIn('> "$cloudflare_public_url_file" <<< "$cloudflare_token"', self.installer)

    def test_managed_hostname_is_user_supplied_not_site_specific(self):
        self.assertIn('remote_url="https://$cloudflare_hostname"', self.installer)
        self.assertIn("ospy.example.com", self.installer)

    def test_cloudflare_quick_tunnel_is_clearly_test_only_and_detects_origin(self):
        self.assertIn("trycloudflare.com", self.installer)
        self.assertIn("testing or temporary access", self.installer)
        self.assertIn(
            "--output /dev/null http://127.0.0.1:8080/",
            self.installer,
        )
        self.assertIn(
            "--output /dev/null https://127.0.0.1:8080/",
            self.installer,
        )
        self.assertIn('cloudflared_origin_options="--url $ospy_origin"', self.installer)
        self.assertIn("--no-tls-verify", self.installer)
        self.assertIn(
            "ExecStart=$cloudflared_path tunnel --no-autoupdate $cloudflared_origin_options",
            self.installer,
        )
        self.assertIn("/etc/systemd/system/ospy-cloudflared-quick.service", self.installer)
        self.assertIn("Restart=on-failure", self.installer)
        self.assertIn("systemctl enable --now ospy-cloudflared-quick.service", self.installer)
        self.assertIn("journalctl -u ospy-cloudflared-quick.service", self.installer)

    def test_tailscale_modes_install_daemon_and_use_local_origin(self):
        self.assertIn("https://tailscale.com/install.sh", self.installer)
        self.assertIn("systemctl enable --now tailscaled.service", self.installer)
        self.assertIn("tailscale up", self.installer)

        self.assertIn(
            "tailscale serve --bg http://127.0.0.1:8080",
            self.installer,
        )
        self.assertIn(
            "tailscale funnel --bg http://127.0.0.1:8080",
            self.installer,
        )
        self.assertIn("tailscale serve status", self.installer)
        self.assertIn("tailscale funnel status", self.installer)

    def test_installer_distinguishes_private_and_public_tailscale_modes(self):
        self.assertIn("Tailscale Serve (private)", self.installer)
        self.assertIn("Tailscale Funnel (public)", self.installer)
        self.assertIn(
            "Only permitted members/devices of your Tailscale network can access it.",
            self.installer,
        )
        self.assertIn(
            "Funnel then publishes OSPy to the public Internet",
            self.installer,
        )

    def test_remote_access_failures_do_not_delete_existing_configuration(self):
        self.assertNotIn("rm -rf /etc/cloudflared", self.installer)
        self.assertNotIn("rm -rf /var/lib/tailscale", self.installer)
        self.assertIn(
            "Existing Cloudflare configuration was not deleted.",
            self.installer,
        )

    def test_remote_access_documentation_matches_installer(self):
        required_sections = (
            "REMOTE ACCESS OPTIONS",
            "## 1. Local network only",
            "## 2. Cloudflare Tunnel",
            "## 3. Cloudflare Quick Tunnel",
            "## 4. Tailscale Serve",
            "## 5. Tailscale Funnel",
            "WHICH REMOTE MODE SHOULD I CHOOSE?",
            "OSPY HTTPS AND TUNNEL HTTPS",
        )
        for heading in required_sections:
            with self.subTest(heading=heading):
                self.assertIn(heading, self.clean_guide)

        self.assertIn("http://127.0.0.1:8080", self.clean_guide)
        self.assertIn("https://127.0.0.1:8080", self.clean_guide)
        self.assertIn("/etc/ospy/cloudflare_public_url", self.clean_guide)
        self.assertIn("No TLS Verify", self.clean_guide)
        self.assertIn("Cloudflare Access", self.clean_guide)
        self.assertIn("trycloudflare.com", self.clean_guide)
        self.assertIn("no Server-Sent Events support", self.clean_guide)
        self.assertIn("tailscale serve --bg http://127.0.0.1:8080", self.clean_guide)
        self.assertIn("tailscale funnel --bg http://127.0.0.1:8080", self.clean_guide)
        self.assertIn("Local network only", self.clean_guide)
        self.assertIn("Cloudflare Tunnel", self.clean_guide)
        self.assertIn("Tailscale Serve", self.clean_guide)
        self.assertIn("Tailscale Funnel", self.clean_guide)

    def test_documentation_explains_domain_and_https_requirements(self):
        self.assertIn("COST AND DOMAIN REQUIREMENTS", self.clean_guide)
        self.assertIn(
            "does not require buying a separate TLS certificate",
            self.clean_guide,
        )
        self.assertIn(
            "A custom public hostname requires a domain",
            self.clean_guide,
        )
        self.assertIn(
            "Cloudflare Quick Tunnel does not require an account or domain",
            self.clean_guide,
        )
        self.assertIn(
            "Tailscale Serve and Tailscale Funnel",
            self.clean_guide,
        )

    def test_installation_documentation_matches_safe_installer_behavior(self):
        docs_root = Path(ROOT) / "ospy" / "docs"
        self.assertIn("git clone", self.installer)
        self.assertIn("stable OSPy `master` branch", self.clean_guide)
        self.assertIn("git pull --ff-only", self.clean_guide)
        self.assertNotIn("git reset --hard", self.clean_guide)
        self.assertIn("Do not delete `ospy/data`", self.clean_guide)

        guides = sorted(docs_root.glob("Web Interface Guide - *.md"))
        self.assertEqual(len(guides), 7)
        for guide in guides:
            text = guide.read_text(encoding="utf-8")
            with self.subTest(guide=guide.name):
                self.assertIn(
                    "wget https://raw.githubusercontent.com/martinpihrt/OSPy/master/ospy_setup.sh",
                    text,
                )
                self.assertIn("sudo bash ospy_setup.sh", text)
                self.assertIn("8080", text)


if __name__ == "__main__":
    unittest.main()
