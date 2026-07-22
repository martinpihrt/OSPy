from pathlib import Path
import unittest

from ospy.helpers import get_help_files


ROOT = Path(__file__).resolve().parents[1]


class HelpDocumentationTests(unittest.TestCase):
    def test_help_templates_offer_current_article_pdf_export(self):
        for template_name in ('help.html', 'help_user.html'):
            content = (ROOT / 'ospy' / 'templates' / template_name).read_text(
                encoding='utf-8'
            )
            self.assertIn('id="helpPdfExport"', content)
            self.assertIn("_('Export help to PDF')", content)

        print_template = ROOT / 'ospy' / 'templates' / 'help_print.html'
        self.assertTrue(print_template.is_file())
        self.assertIn('$:rendered', print_template.read_text(encoding='utf-8'))
        script = (ROOT / 'static' / 'scripts' / 'help.js').read_text(encoding='utf-8')
        self.assertIn('window.location.hash', script)
        self.assertIn("'/help?pdf='", script)

    def test_automated_test_guide_is_listed_in_help(self):
        expected = Path("tests") / "README.md"
        documents = [
            Path(item[2])
            for item in get_help_files()
            if len(item) > 2
        ]
        self.assertIn(expected, documents)
        self.assertTrue((ROOT / expected).is_file())


if __name__ == "__main__":
    unittest.main()
