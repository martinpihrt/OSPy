import os
import tempfile
import time
import unittest

from ospy.translation_status import translation_coverage


class TranslationStatusTests(unittest.TestCase):
    languages = {
        "en_US": "English",
        "complete": "Complete",
        "partial": "Partial",
        "large_gap": "Large gap",
    }

    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary_directory.cleanup)
        self.localedir = self.temporary_directory.name
        self._write_catalog(
            "ospy_messages.pot",
            [("one", ""), ("two", ""), ("three", ""),
             ("four", ""), ("five", "")],
        )

    def _write_catalog(self, relative_path, messages):
        path = os.path.join(self.localedir, relative_path)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as catalog:
            catalog.write('msgid ""\nmsgstr ""\n\n')
            for msgid, msgstr in messages:
                catalog.write('msgid "{}"\nmsgstr "{}"\n\n'.format(
                    msgid, msgstr,
                ))
        return path

    def _write_language(self, locale, messages):
        return self._write_catalog(
            os.path.join(locale, "LC_MESSAGES", "ospy_messages.po"),
            messages,
        )

    def test_each_language_gets_its_own_threshold_status(self):
        self._write_language(
            "complete", [(value, value) for value in
                         ("one", "two", "three", "four", "five")],
        )
        self._write_language(
            "partial", [("one", "1"), ("two", "2"), ("three", "3"),
                        ("four", "4"), ("five", "")],
        )
        self._write_language(
            "large_gap", [("one", "1"), ("two", "2"), ("three", "3")],
        )

        result = translation_coverage(
            self.localedir, self.languages, use_cache=False,
        )
        languages = {item["locale"]: item for item in result["languages"]}

        self.assertEqual(languages["en_US"]["status"], "ok")
        self.assertEqual(languages["complete"]["missing"], 0)
        self.assertEqual(languages["complete"]["status"], "ok")
        self.assertEqual(languages["partial"]["percent"], 80.0)
        self.assertEqual(languages["partial"]["status"], "warning")
        self.assertEqual(languages["large_gap"]["percent"], 60.0)
        self.assertEqual(languages["large_gap"]["status"], "error")
        self.assertEqual(result["status"], "error")

    def test_fuzzy_translation_is_counted_as_missing(self):
        path = self._write_language(
            "complete", [(value, value) for value in
                         ("one", "two", "three", "four", "five")],
        )
        with open(path, "w", encoding="utf-8") as catalog:
            catalog.write(
                'msgid ""\nmsgstr ""\n\n'
                '#, fuzzy\nmsgid "one"\nmsgstr "jedna"\n\n'
                'msgid "two"\nmsgstr "dva"\n\n'
                'msgid "three"\nmsgstr "tri"\n\n'
                'msgid "four"\nmsgstr "ctyri"\n\n'
                'msgid "five"\nmsgstr "pet"\n\n'
                '#~ msgid "obsolete"\n#~ msgstr "stare"\n'
            )
        self._write_language("partial", [])
        self._write_language("large_gap", [])

        result = translation_coverage(
            self.localedir, self.languages, use_cache=False,
        )
        complete = next(
            item for item in result["languages"]
            if item["locale"] == "complete"
        )

        self.assertEqual(complete["missing"], 1)
        self.assertEqual(complete["status"], "warning")

    def test_missing_catalog_is_reported_without_crashing(self):
        result = translation_coverage(
            self.localedir, {"en_US": "English", "missing": "Missing"},
            use_cache=False,
        )
        missing = result["languages"][1]

        self.assertEqual(missing["translated"], 0)
        self.assertEqual(missing["missing"], 5)
        self.assertEqual(missing["status"], "error")
        self.assertTrue(missing["error"])

    def test_cached_result_is_invalidated_when_catalog_changes(self):
        path = self._write_language("complete", [("one", "one")])
        languages = {"en_US": "English", "complete": "Complete"}
        first = translation_coverage(self.localedir, languages)

        time.sleep(0.01)
        self._write_language(
            "complete", [(value, value) for value in
                         ("one", "two", "three", "four", "five")],
        )
        os.utime(path, None)
        second = translation_coverage(self.localedir, languages)

        self.assertEqual(first["languages"][1]["missing"], 4)
        self.assertEqual(second["languages"][1]["missing"], 0)


if __name__ == "__main__":
    unittest.main()
