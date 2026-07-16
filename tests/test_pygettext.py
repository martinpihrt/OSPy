import ast
import glob
import hashlib
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest
import warnings


ROOT = Path(__file__).resolve().parents[1]
POT_PATH = ROOT / "i18n" / "ospy_messages.pot"
PYGETTEXT_INPUTS = (
    "ospy/*.py",
    "ospy/templates/*.html",
    "plugins/*.py",
    "plugins/*/*.py",
    "plugins/*/templates/*.html",
    "setup.py",
    "back_door.py",
    "api/api.py",
    "api/utils.py",
    "web/session.py",
)
HTML_GETTEXT_RE = re.compile(r"(?<![\w.])_\s*\(")


def _contains_python_gettext_call(filename):
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            tree = ast.parse(
                filename.read_text(encoding="utf-8-sig"), filename=str(filename)
            )
    except (SyntaxError, UnicodeDecodeError):
        return False
    return any(
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "_"
        for node in ast.walk(tree)
    )


def _contains_html_gettext_call(filename):
    try:
        source = filename.read_text(encoding="utf-8-sig")
    except UnicodeDecodeError:
        return False
    return HTML_GETTEXT_RE.search(source) is not None


def _project_translation_sources():
    candidates = set(ROOT.glob("*.py"))
    for directory in ("ospy", "api", "plugins", "web"):
        candidates.update((ROOT / directory).rglob("*.py"))
        candidates.update((ROOT / directory).rglob("*.html"))

    result = set()
    for filename in candidates:
        if filename == ROOT / "pygettext.py":
            continue
        if "tests" in filename.relative_to(ROOT).parts:
            continue
        if filename.suffix == ".py" and _contains_python_gettext_call(filename):
            result.add(filename.resolve())
        elif filename.suffix == ".html" and _contains_html_gettext_call(filename):
            result.add(filename.resolve())
    return result


def _expanded_documented_inputs():
    result = set()
    for pattern in PYGETTEXT_INPUTS:
        matches = glob.glob(str(ROOT / pattern))
        result.update(Path(match).resolve() for match in matches if Path(match).is_file())
    return result


def _digest(filename):
    return hashlib.sha256(filename.read_bytes()).hexdigest()


class PygettextTests(unittest.TestCase):
    def test_documented_input_paths_cover_all_translation_sources(self):
        missing = sorted(
            _project_translation_sources() - _expanded_documented_inputs(),
            key=lambda filename: str(filename),
        )
        self.assertFalse(
            missing,
            "The i18n extraction command does not include:\n{}".format(
                "\n".join(str(filename.relative_to(ROOT)) for filename in missing)
            ),
        )

    def test_pygettext_generates_pot_without_modifying_repository_catalog(self):
        original_digest = _digest(POT_PATH)

        with tempfile.TemporaryDirectory(prefix="ospy-pygettext-") as temp_dir:
            output = Path(temp_dir) / "ospy_messages.pot"
            command = [
                sys.executable,
                str(ROOT / "pygettext.py"),
                "-a",
                "-d",
                "messages",
                "-o",
                str(output),
            ]
            command.extend(PYGETTEXT_INPUTS)
            result = subprocess.run(
                command,
                cwd=str(ROOT),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=120,
            )

            self.assertEqual(
                result.returncode,
                0,
                "pygettext.py failed:\n{}\n{}".format(result.stdout, result.stderr),
            )
            self.assertTrue(output.is_file(), "pygettext.py did not create a POT file.")
            generated = output.read_text(encoding="utf-8")
            self.assertIn('msgid "Diagnostics"', generated)
            self.assertIn('msgid "Plug-in manifest is invalid."', generated)
            self.assertIn(
                'msgid "WARNING: This local recovery script resets the OSPy administrator login."',
                generated,
            )

        self.assertEqual(
            _digest(POT_PATH),
            original_digest,
            "The test modified i18n/ospy_messages.pot.",
        )


if __name__ == "__main__":
    unittest.main()
