OSPy Changelog
====

Older changelog entries are archived in [Changelog_old_to_2026-07-02.md](https://github.com/martinpihrt/OSPy/blob/master/ospy/docs/Changelog_old_to_2026-07-02.md).

July 06 2026 (v3.0)
-----------
(martinpihrt)<br/>
Clarified SSL certificate selection in all web interface manuals and the clean installation guide: a local own certificate now has priority, Let’s Encrypt is used otherwise, and enabling both HTTPS options no longer causes a silent HTTP fallback.
Improved home page countdown refresh reliability by adding timeouts and automatic retry to station status polling, and by calculating countdown timers from the real target time so they recover after browser throttling or a stalled request.
Added priority-aware I2C transaction scheduling so time-sensitive plug-ins can request high-priority bus access while display-only updates can run at lower priority.
Persisted plug-in rain delay blocks across OSPy restarts, so active delays set by extensions such as CHMI or tank monitors are restored when their remaining time has not expired.

July 04 2026 (v3.0)
-----------
(martinpihrt)<br/>
Added graph range buttons and date/time filtering to sensor graph pages, matching the graphical filtering controls used by plug-in charts. Synchronized the English, German, Polish, Russian, Serbian, and Slovak Web Interface Guide documents with the detailed Czech guide while preserving existing UI labels such as button names.

July 03 2026 (v3.0)
-----------
(martinpihrt)<br/>
Czech and Slovak language update. Fixed live home page plug-in data refresh so values are rebuilt from current plug-in runtime data instead of being updated by stale list positions. This prevents data from one plug-in being shown under another plug-in after a plug-in hides or clears its home/footer data. Updated the Thermostat plug-in so stopping a selected program also cancels matching Run-Now activity and turns off active stations belonging to that program. The Thermostat status log now clears the old disabled message when the plug-in is enabled again. Improved the login page reset session action so it closes, removes, and reopens the session database while OSPy is running, which can recover from a stuck session store without restarting OSPy. Improved the Programs page with a compact per-group run-order overview based on the scheduler output, added a divider below group action buttons, and replaced remaining checkboxes in the program editor with switch-style controls. Refined the program run-order overview with a label, a divider below the overview, and a non-green block color so it is visually distinct from action buttons.
