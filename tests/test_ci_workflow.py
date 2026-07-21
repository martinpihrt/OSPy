from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "tests.yml"


class ContinuousIntegrationWorkflowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.workflow = WORKFLOW.read_text(encoding="utf-8")

    def test_supported_and_latest_python_versions_are_required(self):
        self.assertIn('          - "3.11"', self.workflow)
        self.assertIn('          - "3.14"', self.workflow)
        self.assertIn("fail-fast: false", self.workflow)
        self.assertIn("name: Python ${{ matrix.python-version }}", self.workflow)
        self.assertIn("python-version: ${{ matrix.python-version }}", self.workflow)
        self.assertNotIn("continue-on-error", self.workflow)

    def test_workflow_uses_current_node24_actions_and_official_plugins(self):
        self.assertIn("uses: actions/checkout@v6", self.workflow)
        self.assertIn("uses: actions/setup-python@v6", self.workflow)
        self.assertIn("repository: martinpihrt/OSPy-plugins", self.workflow)
        self.assertIn("OSPY_PLUGIN_ROOTS:", self.workflow)
        self.assertNotIn("web.py==", self.workflow)


if __name__ == "__main__":
    unittest.main()
