OSPy Changelog
====

Older changelog entries are archived in [Changelog_old_to_2026-07-02.md](https://github.com/martinpihrt/OSPy/blob/master/ospy/docs/Changelog_old_to_2026-07-02.md).

July 10 2026 (v3.0)
-----------
(martinpihrt)<br/>
Added in-memory CPU history to the Diagnostics page. Each plug-in now keeps a rolling one-week CPU usage history in RAM only, the CPU column includes a History button, and the diagnostics page can show a chart for the selected plug-in with 1 hour, 24 hour, and 7 day filters without writing diagnostic samples to disk. Updated the Czech OSPy translation.

July 09 2026 (v3.0)
-----------
(martinpihrt)<br/>
Improved the Diagnostics page layout with a wider system summary, clearer labels, grid lines in the plug-in table, and a corrected restart button label for plug-in restarts. Added a plug-in sort selector with CPU load as the default order, plus sorting by plug-in name or total CPU time. Diagnostics refresh errors are now cleared after a successful refresh, and the live diagnostics API reports controlled JSON errors instead of leaving the page with a stale warning. Added Diagnostics documentation to all Web Interface Guides, expanded the i18n README with step-by-step Poedit instructions, changed `pygettext.py` so HTML templates are scanned only for `_()` translation calls, preventing normal HTML/CSS markup from breaking POT generation, and updated the Czech OSPy translation. Refined the Programs page so program dividers sit below each program's action buttons, the run-order overview uses an orange dashed style distinct from action buttons, and run-order tooltips are available by keyboard focus or touch as well as mouse hover.

July 08 2026 (v3.0)
-----------
(martinpihrt)<br/>
Added an admin Diagnostics page linked from the footer, with live-refreshing system/process metrics, plug-in thread CPU diagnostics, links to plug-in pages and System Information when available, and a CSRF-protected restart action for running plug-ins. Fixed IP Cam home pictures so large cached JPG/GIF files stay as small station thumbnails while the click-through viewer opens a bounded preview. Hardened station image handling by replacing the old web-triggered `sudo pip install Pillow` command with a fixed `apt-get install -y python3-pil` call without shell execution, and by validating uploaded images through Pillow with decompression-bomb protection and safer error handling.

July 07 2026 (v3.0)
-----------
(martinpihrt)<br/>
Fixed plug-in repository document synchronization during plug-in install and update. OSPy now detects the real root of the GitHub plug-in archive and copies the repository README and CHANGELOG into the local `plugins` directory, so the Help page shows the current plug-in changelog after plug-in updates.

July 06 2026 (v3.0)
-----------
(martinpihrt)<br/>
Added a station picture source option for the home page so the existing station image display can continue using uploaded station images or, when selected, cached IP Cam JPG/GIF images through the core image endpoint with fallback to station images. If the IP Cam plug-in is not installed or has no cached image for a station, the home page falls back to the normal station image. The core image endpoint now handles this fallback directly, so the home page does not depend on the IP Cam plug-in route being available.
Clarified SSL certificate selection in all web interface manuals and the clean installation guide: a local own certificate now has priority, Let’s Encrypt is used otherwise, and enabling both HTTPS options no longer causes a silent HTTP fallback.
Improved home page countdown refresh reliability by adding timeouts and automatic retry to station status polling, and by calculating countdown timers from the real target time so they recover after browser throttling or a stalled request.
Added priority-aware I2C transaction scheduling so time-sensitive plug-ins can request high-priority bus access while display-only updates can run at lower priority.
Persisted plug-in rain delay blocks across OSPy restarts, so active delays set by extensions such as CHMI or tank monitors are restored when their remaining time has not expired.
Added the plug-in repository changelog to the Help page Plug-ins section when `plugins/CHANGELOG.md` is available, and copy the plug-in repository README and changelog into the local `plugins` directory during plug-in installs or updates.

July 04 2026 (v3.0)
-----------
(martinpihrt)<br/>
Added graph range buttons and date/time filtering to sensor graph pages, matching the graphical filtering controls used by plug-in charts. Synchronized the English, German, Polish, Russian, Serbian, and Slovak Web Interface Guide documents with the detailed Czech guide while preserving existing UI labels such as button names.

July 03 2026 (v3.0)
-----------
(martinpihrt)<br/>
Czech and Slovak language update. Fixed live home page plug-in data refresh so values are rebuilt from current plug-in runtime data instead of being updated by stale list positions. This prevents data from one plug-in being shown under another plug-in after a plug-in hides or clears its home/footer data. Updated the Thermostat plug-in so stopping a selected program also cancels matching Run-Now activity and turns off active stations belonging to that program. The Thermostat status log now clears the old disabled message when the plug-in is enabled again. Improved the login page reset session action so it closes, removes, and reopens the session database while OSPy is running, which can recover from a stuck session store without restarting OSPy. Improved the Programs page with a compact per-group run-order overview based on the scheduler output, added a divider below group action buttons, and replaced remaining checkboxes in the program editor with switch-style controls. Refined the program run-order overview with a label, a divider below the overview, and a non-green block color so it is visually distinct from action buttons.
