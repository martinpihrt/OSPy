OSPy Plug-ins
====

The basic structure is as follows:

    plugins
    + plugin_name
      + data
      + docs
      + static
      * script
      + templates
      + __init__.py
      + plugin.json
      \ README.md

The static files will be made accessible automatically at the following location:
/plugins/plugin_name/static/...
The script files will be made accessible automatically at the following location:
/plugins/plugin_name/script/... Inject own plugin javascript to call our API for data and modify the display (in base.html)

All *.md files in the docs directory will be visible in the help page.
The README.md (if available) will be the first entry in the help page
and might be used in the future as a description for plug-in browsing.

Optional plugin.json manifest
----

Plug-ins can provide an optional UTF-8 `plugin.json` file. Existing plug-ins
without it continue to use `NAME` and `MENU` from `__init__.py`.

    {
      "schema_version": 1,
      "id": "plugin_name",
      "name": "Human-readable name",
      "menu": "Menu label",
      "version": "1.0.0",
      "description": "Short plug-in description.",
      "author": "Author name",
      "homepage": "https://example.com/plugin",
      "license": "MIT"
    }

The `id` must match the plug-in directory. Unknown fields are retained for
forward-compatible metadata. The reserved `ospy`, `python`, `requirements`,
`hardware`, `permissions`, and `conflicts` sections will be used by later
compatibility checks. Invalid or oversized manifests are ignored and OSPy
falls back to the legacy metadata.
