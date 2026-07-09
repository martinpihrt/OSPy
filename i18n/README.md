I18N language localisation
====

This directory contains translations for the OSPy web interface.

OSPy uses GNU gettext files:

* `ospy_messages.pot` - translation template generated from the source code.
* `ospy_messages.po` - editable translation file for one language.
* `ospy_messages.mo` - compiled translation file used by OSPy at runtime.

Recommended editor: [Poedit](https://poedit.net/).

----

# Folder structure

Each language has its own directory:

```text
i18n/
  ospy_messages.pot
  cs_CZ/
    LC_MESSAGES/
      ospy_messages.po
      ospy_messages.mo
  de_DE/
    LC_MESSAGES/
      ospy_messages.po
      ospy_messages.mo
```

The directory name is the locale code. Examples:

* `cs_CZ` - Czech
* `de_DE` - German
* `en_US` - English
* `pl_PL` - Polish
* `ru_RU` - Russian
* `sk_SK` - Slovak
* `sr_RS` - Serbian

----

# 1. Generate a new POT template

Run this command from the OSPy root directory:

```bash
python3 pygettext.py -a -v -d messages -o i18n/ospy_messages.pot ospy/*.py ospy/templates/*.html plugins/*/*.py plugins/*/templates/*.html setup.py api/api.py api/utils.py web/session.py
```

The output file is:

```text
i18n/ospy_messages.pot
```

This file contains all strings marked for translation with `_('text')`.

Do not translate directly in the `.pot` file. Use it as a template for `.po` files.

----

# 2. Create a new translation in Poedit

Use this when adding a new language.

1. Open Poedit.
2. Select **File -> New from POT/PO file...**.
3. Open `i18n/ospy_messages.pot`.
4. Select the target language.
5. Translate the strings.
6. Save the file as:

```text
i18n/<locale>/LC_MESSAGES/ospy_messages.po
```

Example for Czech:

```text
i18n/cs_CZ/LC_MESSAGES/ospy_messages.po
```

When saving, Poedit also creates or updates:

```text
i18n/<locale>/LC_MESSAGES/ospy_messages.mo
```

The `.mo` file is the compiled file that OSPy uses.

----

# 3. Update an existing translation in Poedit

Use this when `ospy_messages.po` already exists and the source code has new strings.

1. Generate a fresh `i18n/ospy_messages.pot`.
2. Open the existing language file in Poedit, for example:

```text
i18n/cs_CZ/LC_MESSAGES/ospy_messages.po
```

3. Select **Translation -> Update from POT file...**.
4. Choose `i18n/ospy_messages.pot`.
5. Poedit adds new strings and marks changed strings as fuzzy if needed.
6. Translate all untranslated and fuzzy strings.
7. Save the file.

After saving, Poedit updates both:

```text
ospy_messages.po
ospy_messages.mo
```

----

# 4. Check the translation in OSPy

1. Copy or keep the `.po` and `.mo` files in the correct locale directory.
2. Restart OSPy.
3. Open the web interface.
4. Go to **Options -> System Section -> Select Language**.
5. Select the language and save.
6. Open the changed pages and check that the text is translated correctly.

If a string is still shown in English, check:

* the string exists in `ospy_messages.po`
* the string is translated
* the entry is not marked as fuzzy
* `ospy_messages.mo` was generated after saving
* OSPy was restarted after updating the `.mo` file

----

# 5. Send or commit the translation

For every changed language include both files:

```text
i18n/<locale>/LC_MESSAGES/ospy_messages.po
i18n/<locale>/LC_MESSAGES/ospy_messages.mo
```

If you are sending the translation by e-mail, send both `.po` and `.mo` files to:

```text
martinpihrt@gmail.com
```

----

# Notes for developers

`pygettext.py` scans Python files and OSPy HTML templates for strings marked with `_()`.

Python files are parsed with Python tokenization. HTML templates are handled differently: the extractor searches only for `_('text')` / `_("text")` calls and ignores the rest of the HTML, CSS and JavaScript markup. This prevents normal HTML indentation, tags or `<style>` blocks from breaking POT generation, while translatable strings inside templates are still collected.

After changing templates or Python code, always check that POT generation still works.
