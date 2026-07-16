from pathlib import Path
import unittest

from ospy.helpers import get_help_files


ROOT = Path(__file__).resolve().parents[1]


class HelpDocumentationTests(unittest.TestCase):
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
