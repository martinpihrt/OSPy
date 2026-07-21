import os
from pathlib import Path
import unittest

import web


ROOT = Path(__file__).resolve().parents[1]
TEMPLATE_ROOT = ROOT / "ospy" / "templates"


def _configured_plugin_roots():
    value = os.environ.get("OSPY_PLUGIN_ROOTS", "")
    return [
        Path(item).expanduser().resolve()
        for item in value.split(os.pathsep)
        if item.strip()
    ]


def _compile_templates(test_case, templates):
    failures = []
    for template in templates:
        try:
            web.template.Template(
                template.read_text(encoding="utf-8"),
                filename=str(template),
            )
        except Exception as error:
            failures.append("{}: {!r}".format(template, error))

    test_case.assertFalse(
        failures,
        "The following web.py templates failed to compile:\n{}".format(
            "\n".join(failures)
        ),
    )


class TemplateCompilationTests(unittest.TestCase):
    def test_expression_before_unmatched_quote_in_text_compiles(self):
        template = web.template.Template("$def with (value)\n$value's status")
        self.assertEqual("test's status\n", str(template(value="test")))

    def test_expression_before_period_and_unmatched_quote_compiles(self):
        template = web.template.Template("$def with (_)\n<p title='$_('status').'>")
        self.assertEqual(
            "<p title='status.'>\n",
            str(template(_=lambda value: value)),
        )

    def test_all_core_templates_compile(self):
        templates = sorted(TEMPLATE_ROOT.glob("*.html"))
        self.assertTrue(templates, "No OSPy templates were found.")
        _compile_templates(self, templates)

    def test_configured_plugin_templates_compile(self):
        for plugin_root in _configured_plugin_roots():
            with self.subTest(plugin_root=str(plugin_root)):
                self.assertTrue(
                    plugin_root.is_dir(),
                    "Configured plug-in root does not exist: {}".format(plugin_root),
                )
                templates = sorted(plugin_root.glob("*/templates/*.html"))
                self.assertTrue(
                    templates,
                    "No plug-in templates were found in {}".format(plugin_root),
                )
                _compile_templates(self, templates)


if __name__ == "__main__":
    unittest.main()
