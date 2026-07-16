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
      "license": "MIT",
      "ospy": {"min": "3.0.0", "max": "3.9.999"},
      "python": {"min": "3.8", "max": "3.13"},
      "requirements": [
        {"module": "smbus2", "package": "smbus2", "required": true}
      ],
      "hardware": {
        "platforms": ["raspberry_pi", "linux"],
        "requires": ["i2c", "gpio"],
        "gpio": [17, 27],
        "i2c": ["0x20"]
      },
      "permissions": ["network", "files", "i2c", "gpio", "email"],
      "conflicts": {
        "plugins": ["another_plugin"]
      }
    }

The `id` must match the plug-in directory. Invalid or oversized manifests are
ignored and OSPy falls back to the legacy metadata.

Before activation OSPy checks the optional minimum and maximum OSPy/Python
versions, required importable Python modules, supported platform and required
I2C/GPIO support. It also compares declared GPIO pins, I2C addresses and
explicit plug-in conflicts with enabled plug-ins. Missing required components
and resource conflicts block activation; optional requirements and unknown
permission names produce warnings. Supported permission names are `network`,
`files`, `i2c`, `gpio`, `email`, `subprocess`, and `system`. Permissions are
declarations shown to the administrator; they are not an operating-system
sandbox.
