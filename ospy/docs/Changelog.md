OSPy Changelog
====

Older changelog entries are archived in [Changelog_old_to_2026-07-02.md](https://github.com/martinpihrt/OSPy/blob/master/ospy/docs/Changelog_old_to_2026-07-02.md).

July 15 2026 (v3.0)
-----------
(martinpihrt)<br/>
Expanded the user-facing Events log without changing the existing technical debug log. Event records now carry a backward-compatible severity and category, use colored textual severity badges, and can be filtered with a single category selector for irrigation, configuration, users and security, system and plug-ins, or sensors and conditions. Date and time columns no longer wrap, old saved records are normalized for display, and `events.csv` now includes Level and Category. Added operational and audit events for manual irrigation actions, blocked scheduled runs and their reasons, program and station configuration, login and two-factor failures with write throttling, user and password administration, system restart and shutdown requests, plug-in management and restart failures, and configured sensor events. Fixed previously saved program-group events being hidden by the old fixed checkbox filters. Documented the expanded Events log in all seven language Web Interface Guides.

Extended the Events log to authenticated API activity. Failed and temporarily blocked API authentication attempts are throttled and recorded as user/security warnings or errors, while state-changing API requests record station and program control, program and station configuration, system-option changes, station-log clearing, run-once scheduling, and restart or shutdown requests in their corresponding categories. Routine reads and successful per-request Basic authentication are intentionally not logged, preventing normal API polling from flooding persistent storage. Updated all seven language Web Interface Guides.

July 14 2026 (v3.0)
-----------
(martinpihrt)<br/>
Fixed the Options page failing to open after the weather location picker update on systems where weather was disabled and latitude/longitude still contained the historical empty-dictionary defaults. Weather coordinates now use empty-string defaults, legacy saved dictionary values are normalized when settings are loaded, and the Options template safely formats coordinate values before adding them to the HTML.

Added a protected Feedback page linked by a new header button next to the OSPy system name. Signed-in administrators and users can prepare a bug report, improvement suggestion, or question; OSPy validates the form and opens a prefilled GitHub issue for review and submission under the user's GitHub account, without storing a GitHub access token. Reports can optionally include a previewed set of non-identifying OSPy version, operating-system, architecture, distribution, and Python details reused from anonymous usage statistics; system names, operator names, IP addresses, and usage-statistics identifiers are excluded. The page also links directly to existing GitHub Issues and GitHub Discussions. The form is CSRF-protected, uses a no-referrer policy, and supports all three themes and mobile layouts.

Updated the Czech OSPy translation. Restyled the Feedback system-information option as the standard green/red OSPy switch used by plug-in settings while preserving keyboard control, and added the existing i18n translation workflow README to the built-in OSPy Help menu as **Translation Guide (i18n)**.

July 12 2026 (v3.0)
-----------
(martinpihrt)<br/>
Separated 2FA setup into method-specific cards and explicit send, verify-and-activate, and disable actions so refreshing or revisiting setup cannot accidentally change the active method. Active TOTP and e-mail methods are now identified in Options, backup codes end with a Done action instead of another Save, and authenticator account labels start with the OSPy site name. The Home weather location card is now compact, transparent, and styled like the other dark-blue bordered sections.

Plug-in CPU history is now sampled in memory every minute by a background thread while OSPy is running, instead of collecting samples only while the Diagnostics page is open. Opening a 1-hour, 24-hour, or 7-day graph therefore immediately shows the available history since OSPy started; the samples are intentionally discarded on restart. The history panel now uses the shared rounded OSPy card style, including the correct border color for each theme and an exact full-width border-box layout.

Restored the visible rounded corners of the Diagnostics system and plug-in tables in all themes by moving their shared OSPy borders to full-width outer cards, where table cells cannot overwrite the rounded corners.

July 11 2026 (v3.0)
-----------
(martinpihrt)<br/>
Added optional two-factor authentication for the main administrator account. Settings now offer one mutually exclusive method: a TOTP authenticator application paired with a QR code, or a short-lived code sent immediately through the running E-mail Notifications SSL plug-in. Password verification and second-factor verification use separate session states, login and QR requests are CSRF-protected, legacy URL password authentication cannot bypass the second factor, remembered browser tokens are issued only after the second factor succeeds and are revoked when the method changes, attempts and challenge lifetime are limited, and one-time backup codes provide account recovery. TOTP verification uses the Python standard library; QR rendering is installed through the normal `python setup.py install` flow rather than a web-triggered package installer. Documented setup, operation, recovery, and dependency handling in all seven language Web Interface Guides. The local back_door.py recovery script now also disables 2FA, removes its secret and backup codes, and invalidates remembered and active web sessions so the generated recovery login works after losing the second factor; the main and service README files now document this emergency procedure. The same README files now document the standalone pre-start relay_test.py hardware-board test, including service shutdown, its all-relays behavior, load-disconnection warning, Ctrl+C cleanup, and normal OSPy restart. Replaced the inline program-group postponement date row with a focused modal date/time dialog, live old/new run preview, native mobile date/time controls, and responsive full-width mobile actions without changing postponement scheduling behavior. Log clearing now returns to the section that initiated the action, and changing event filters keeps the Events section open instead of reopening the Station log.

Added an interactive, mobile-friendly weather location picker to Options using a locally bundled Leaflet 1.9.4 library and correctly attributed OpenStreetMap tiles. Administrators can click an exact point or explicitly request the browser device location, review coordinates, and save them through the existing CSRF-protected Options form with server-side latitude/longitude validation. Manual coordinates are now authoritative for Stormglass and form part of its cache key, while editing the text location switches back to Nominatim search. Fixed the weather thread incorrectly forcing a successful location status after lookup failures. Replaced the technical Home weather line with a responsive location card, internal read-only map, admin edit shortcut, status, and collapsible coordinate details. Updated all seven language Web Interface Guides.

Updated the Czech OSPy translation. 2FA login is not 100% finished and will still be adjusted!

July 10 2026 (v3.0)
-----------
(martinpihrt)<br/>
Added in-memory CPU history to the Diagnostics page. Each plug-in now keeps a rolling one-week CPU usage history in RAM only, the CPU column includes a History button, and the diagnostics page can show a chart for the selected plug-in with 1 hour, 24 hour, and 7 day filters without writing diagnostic samples to disk. Added a secure one-time program group postponement action: an administrator can move each enabled program's nearest group run to a new date and start time while preserving run order, durations, and relative gaps without changing later regular schedules. Postponements survive service restarts, continue to respect scheduler, rain, station-delay, and output-usage rules, can be safely cancelled, and are protected by CSRF verification and server-side validation. Documented group postponement in all language Web Interface Guides. Fixed a race during remembered browser login that could randomly cause a redirect loop until the OSPy service was restarted, and prevented concurrent requests from recording the same remembered login multiple times in the event log. Updated the Czech OSPy translation.

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
