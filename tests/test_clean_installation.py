import os
from pathlib import Path
import shutil
import subprocess
import unittest


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INSTALLER = os.path.join(ROOT, "ospy_setup.sh")
SERVICE = os.path.join(ROOT, "service", "ospy.service")


class CleanInstallationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open(INSTALLER, "r", encoding="utf-8") as source:
            cls.installer = source.read()
        with open(SERVICE, "r", encoding="utf-8") as source:
            cls.service = source.read()

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

    def test_installation_documentation_matches_safe_installer_behavior(self):
        docs_root = Path(ROOT) / "ospy" / "docs"
        clean_guide = (docs_root / "Clean_installation.md").read_text(encoding="utf-8")
        self.assertIn("git clone", self.installer)
        self.assertIn("stable OSPy `master` branch", clean_guide)
        self.assertIn("git pull --ff-only", clean_guide)
        self.assertNotIn("git reset --hard", clean_guide)
        self.assertIn("Do not delete `ospy/data`", clean_guide)

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
