from pathlib import Path
import os
import unittest


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "tests.yml"


def _plugin_workflow():
    candidates = []
    configured_roots = os.environ.get("OSPY_PLUGIN_ROOTS", "")
    for configured_root in configured_roots.split(os.pathsep):
        if configured_root:
            candidates.append(
                Path(configured_root).resolve().parent
                / ".github"
                / "workflows"
                / "tests.yml"
            )
    candidates.append(
        ROOT.parent / "OSPy-plugins" / ".github" / "workflows" / "tests.yml"
    )
    return next((candidate for candidate in candidates if candidate.is_file()), None)


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

    def test_official_plugin_workflow_covers_python_and_ospy_matrix(self):
        plugin_workflow = _plugin_workflow()
        if plugin_workflow is None:
            self.skipTest("The official OSPy-plugins checkout is not available.")

        workflow = plugin_workflow.read_text(encoding="utf-8")
        self.assertIn('          - "3.11"', workflow)
        self.assertIn('          - "3.14"', workflow)
        self.assertIn("          - master", workflow)
        self.assertIn("          - beta", workflow)
        self.assertIn("fail-fast: false", workflow)
        self.assertIn(
            "name: Python ${{ matrix.python-version }} / OSPy ${{ matrix.ospy-branch }}",
            workflow,
        )
        self.assertIn("python-version: ${{ matrix.python-version }}", workflow)
        self.assertNotIn("continue-on-error", workflow)


if __name__ == "__main__":
    unittest.main()
