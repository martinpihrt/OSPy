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
      \ README.md

The static files will be made accessible automatically at the following location:
/plugins/plugin_name/static/...
The script files will be made accessible automatically at the following location:
/plugins/plugin_name/script/... Inject own plugin javascript to call our API for data and modify the display (in base.html)

All *.md files in the docs directory will be visible in the help page.
The README.md (if available) will be the first entry in the help page
and might be used in the future as a description for plug-in browsing.