from pathlib import Path
import hashlib
import unittest


ROOT = Path(__file__).resolve().parents[1]
TOPICS = (
    'programs',
    'startDecision',
    'master',
    'weather',
    'sensors',
    'plugins',
    'update',
    'storage',
    'backup',
)


class DiagnosticsDiagramTests(unittest.TestCase):
    def test_diagnostics_exposes_all_local_diagram_topics(self):
        template = (ROOT / 'ospy' / 'templates' / 'diagnostics.html').read_text(
            encoding='utf-8'
        )
        self.assertIn('id="systemDiagramSection"', template)
        self.assertIn('/static/scripts/mermaid-10.9.6.min.js', template)
        self.assertNotIn('cdn.jsdelivr.net', template)
        for topic in TOPICS:
            self.assertIn('value="{}"'.format(topic), template)

    def test_diagram_controller_keeps_trusted_strict_rendering_and_exports(self):
        script = (
            ROOT / 'static' / 'scripts' / 'diagnostics-diagrams.js'
        ).read_text(encoding='utf-8')
        for topic in TOPICS:
            self.assertIn('{}: {{'.format(topic), script)
        self.assertIn("securityLevel: 'strict'", script)
        self.assertIn("downloadBlob(svgBlob(), 'svg')", script)
        self.assertIn("canvas.toBlob", script)
        self.assertIn("window.print()", script)

    def test_pinned_mermaid_bundle_and_license_are_present(self):
        bundle = ROOT / 'static' / 'scripts' / 'mermaid-10.9.6.min.js'
        license_file = ROOT / 'static' / 'scripts' / 'mermaid-LICENSE.txt'
        self.assertGreater(bundle.stat().st_size, 1_000_000)
        self.assertEqual(
            hashlib.sha256(bundle.read_bytes()).hexdigest(),
            'eda3a0ad572bbe69a318c1be0163e8233dd824f3f12939e5168feba207767151',
        )
        self.assertIn('MIT License', license_file.read_text(encoding='utf-8'))

    def test_all_themes_style_diagrams_and_pdf_icon_is_complete(self):
        for theme in ('basic', 'blue', 'dark'):
            css = (
                ROOT / 'static' / 'themes' / theme / 'theme.css'
            ).read_text(encoding='utf-8')
            self.assertIn('.systemDiagramCanvas', css)
            self.assertIn('.diagramWideMode', css)
            self.assertIn('body.diagramPrintMode', css)
        pdf_icon = (ROOT / 'static' / 'images' / 'pdf.svg').read_text(
            encoding='utf-8'
        )
        self.assertIn('>PDF</text>', pdf_icon)


if __name__ == '__main__':
    unittest.main()
