import ast
import os
from pathlib import Path
import unittest

from tests.test_support import TEST_DATA_DIR  # noqa: F401


ROOT = Path(__file__).resolve().parents[1]


def _official_plugin_roots():
    roots = []
    configured = os.environ.get("OSPY_PLUGIN_ROOTS", "")
    if configured:
        roots.extend(
            Path(item).expanduser().resolve()
            for item in configured.split(os.pathsep)
            if item.strip()
        )
    sibling = ROOT.parent / "OSPy-plugins" / "plugins"
    if sibling.is_dir():
        roots.append(sibling)
    return list(dict.fromkeys(roots))


def _plugin_sources():
    for root in _official_plugin_roots():
        for directory in sorted(root.iterdir()):
            source = directory / "__init__.py"
            if source.is_file():
                yield directory.name, source


def _call_name(call):
    try:
        return ast.unparse(call.func)
    except Exception:
        return ""


class PluginIsolationTests(unittest.TestCase):
    def test_plugins_do_not_connect_signals_during_module_import(self):
        violations = []
        for plugin, source in _plugin_sources():
            tree = ast.parse(
                source.read_text(encoding="utf-8-sig"), filename=str(source)
            )
            for statement in tree.body:
                if isinstance(statement, ast.Expr) and isinstance(
                        statement.value, ast.Call):
                    name = _call_name(statement.value)
                    if name.endswith(".connect"):
                        violations.append(
                            "{}:{} {}".format(
                                plugin, statement.lineno, name
                            )
                        )
        self.assertEqual(violations, [])

    def test_plugins_do_not_change_outputs_during_module_import(self):
        violations = []
        risky_prefixes = (
            "stations.activate",
            "stations.deactivate",
            "stations.clear",
            "outputs.",
        )
        for plugin, source in _plugin_sources():
            tree = ast.parse(
                source.read_text(encoding="utf-8-sig"), filename=str(source)
            )
            for statement in tree.body:
                if isinstance(
                        statement,
                        (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef),
                ):
                    continue
                for call in ast.walk(statement):
                    if not isinstance(call, ast.Call):
                        continue
                    name = _call_name(call)
                    if name.startswith(risky_prefixes):
                        violations.append(
                            "{}:{} {}".format(plugin, call.lineno, name)
                        )
        self.assertEqual(violations, [])

    def test_plugin_http_requests_have_a_timeout(self):
        violations = []
        network_calls = {
            "requests.get",
            "requests.post",
            "requests.put",
            "requests.delete",
            "urllib.request.urlopen",
            "urlopen",
        }
        for plugin, source in _plugin_sources():
            tree = ast.parse(
                source.read_text(encoding="utf-8-sig"), filename=str(source)
            )
            for call in ast.walk(tree):
                if not isinstance(call, ast.Call):
                    continue
                name = _call_name(call)
                if name not in network_calls:
                    continue
                if not any(keyword.arg == "timeout" for keyword in call.keywords):
                    violations.append(
                        "{}:{} {}".format(plugin, call.lineno, name)
                    )
        self.assertEqual(violations, [])


if __name__ == "__main__":
    unittest.main()
