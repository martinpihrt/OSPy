from pathlib import Path
import subprocess
import sys
import textwrap
import unittest


ROOT = Path(__file__).resolve().parents[1]


class RemovedCgiCompatibilityTests(unittest.TestCase):
    def test_webapi_imports_local_fallback_when_stdlib_cgi_is_missing(self):
        script = textwrap.dedent(
            """
            import builtins

            original_import = builtins.__import__

            def import_without_cgi(name, globals=None, locals=None, fromlist=(), level=0):
                if level == 0 and name == "cgi":
                    raise ModuleNotFoundError("No module named 'cgi'", name="cgi")
                return original_import(name, globals, locals, fromlist, level)

            builtins.__import__ = import_without_cgi

            import web.webapi

            assert web.webapi.cgiFieldStorage.__mro__[1].__module__ == "web.cgi_compat"
            """
        )
        result = subprocess.run(
            [sys.executable, "-c", script],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            timeout=30,
        )
        self.assertEqual(
            result.returncode,
            0,
            "Fallback import failed:\nstdout:\n{}\nstderr:\n{}".format(
                result.stdout, result.stderr
            ),
        )


if __name__ == "__main__":
    unittest.main()
