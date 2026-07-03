OSPy Changelog
====

Older changelog entries are archived in [https://github.com/martinpihrt/OSPy/blob/master/ospy/docs/Changelog_old_to_2026-07-02.md](Changelog_old_to_2026-07-02.md).

July 03 2026 (v3.0)
-----------
(martinpihrt)<br/>
Czech and Slovak language update. Fixed live home page plug-in data refresh so values are rebuilt from current plug-in runtime data instead of being updated by stale list positions. This prevents data from one plug-in being shown under another plug-in after a plug-in hides or clears its home/footer data. Updated the Thermostat plug-in so stopping a selected program also cancels matching Run-Now activity and turns off active stations belonging to that program. The Thermostat status log now clears the old disabled message when the plug-in is enabled again. Improved the login page reset session action so it closes, removes, and reopens the session database while OSPy is running, which can recover from a stuck session store without restarting OSPy. Improved the Programs page with a compact per-group run-order overview based on the scheduler output, added a divider below group action buttons, and replaced remaining checkboxes in the program editor with switch-style controls. Refined the program run-order overview with a label, a divider below the overview, and a non-green block color so it is visually distinct from action buttons.
