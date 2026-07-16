OSPy automated tests
====

Run the core tests from the OSPy root directory:

```bash
python3 -m unittest discover -s tests -v
```

The suite checks:

* compilation of every core web.py HTML template;
* completeness and execution of the documented `pygettext.py` command;
* protection of the repository POT file during the extraction test;
* manifest parser acceptance and rejection rules;
* every `plugin.json` found in the installed OSPy `plugins` directory.
* archive installation blocking before file writes for missing, invalid or
  incompatible manifests;
* partial bulk installation, compatibility warnings and automatic-update
  blocking.

To additionally compile all plug-in templates and require and validate a
manifest for every plug-in in the separate official OSPy-plugins repository,
provide its `plugins` directory:

```bash
OSPY_PLUGIN_ROOTS=/path/to/OSPy-plugins/plugins python3 -m unittest discover -s tests -v
```

Multiple plug-in roots can be separated with the operating system path
separator (`:` on Linux, `;` on Windows).
