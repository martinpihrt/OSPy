# OSPy-plugins Changelog

July 10 2026
-----------
(Martin Pihrt) - LCD Display<br/>
Fixed a condition where LCD notifications could leave the plug-in blocked and spinning without sleep, causing near-100% CPU until the plug-in was restarted. Temporary LCD notification blocks now sleep and automatically expire, so normal display updates resume without manual restart.

(Martin Pihrt) - OSPy package Backup<br/>
Improved backup ZIP downloads for larger files. Backup downloads now include Content-Length and stream the ZIP in chunks instead of loading the whole file into memory before sending it to the browser.

(Martin Pihrt) - Home Assistant<br/>
Adjusted the Home Assistant status output for DS1-DS6 sensors. The plug-in no longer writes the initial all--127 DS block that can appear before the Air Temperature and Humidity Monitor has completed its first successful read, while real later values are still shown. Signal updates now also return quietly until Home Assistant devices are initialized.

(Martin Pihrt) - OSPy package Backup<br/>
Fixed the backup page actions after the file-handling hardening. Backup, delete, download, and error notices can again use the translation helper correctly, so pressing the backup/delete buttons no longer breaks the settings page.

(Martin Pihrt) - Database Connector<br/>
Restored database backup compatibility with MariaDB/MySQL dump tools that do not accept the connect-timeout option. The backup command now uses the same mysqldump argument set as before, while the Python process timeout remains in place to prevent a stuck backup.

July 09 2026
-----------
(Martin Pihrt) - Wind Speed Monitor<br/>
Hardened Wind Speed Monitor without changing its high-priority I2C measurement path. Numeric wind/log/event settings and selected stations/programs are clamped before use, repeated runtime/e-mail errors are throttled, damaged local JSON logs return empty data, settings/status JSON works when the background thread is not running, and graph timestamp parsing was updated for Python 3.

(Martin Pihrt) - Webcam Monitor<br/>
Hardened Webcam Monitor capture/download handling. Missing fswebcam no longer triggers automatic apt installation; the plug-in now logs the fixed apt command instead. Camera resolution is validated before use, fswebcam is executed with an argument list instead of a string-built command, and downloaded snapshots are served from the file in binary mode with a safe fallback content type.

(Martin Pihrt) - Weather Stations<br/>
Hardened Weather Stations settings and data JSON. Canvas/text sizes are clamped, all 30 sensor configuration lists are normalized to consistent lengths and safe value types before rendering/saving, malformed form numbers fall back to defaults, and per-sensor read failures in data_json return -127 without repeatedly writing tracebacks.

(Martin Pihrt) - Weather Dashboard<br/>
Renamed the plug-in from weather dashboard to Weather Dashboard and hardened dashboard settings. Gauge count, size/font values, source/type/channel selections, names, units, tick labels, and colored ranges are now normalized before saving/rendering so malformed form data cannot break the dashboard JSON or canvas page.

(Martin Pihrt) - Weather-based Water Level Netatmo<br/>
Hardened Weather-based Water Level Netatmo. Netatmo credentials are now read from current settings instead of stale import-time defaults, Netatmo secret/password are masked in settings JSON, water level/weather/Netatmo numeric settings are clamped before use, empty weather or Netatmo measure data no longer causes division/unpack errors, and repeated runtime/API errors are throttled.

(Martin Pihrt) - Weather-based Water Level<br/>
Hardened Weather-based Water Level settings normalization. Water level min/max, history/forecast day counts, freeze protection temperature/minutes, station list, and month list are now clamped before calculations and after saving settings so web form values cannot break the hourly calculation loop.

(Martin Pihrt) - Weather-based Rain Delay<br/>
Hardened Weather-based Rain Delay and Netatmo handling. Netatmo credentials are now read from current settings instead of stale import-time defaults, Netatmo secret/password are masked in settings JSON, delay/Netatmo intervals are clamped before use, repeated runtime/API errors are throttled, empty Netatmo measure responses are handled safely, and footer text no longer depends on precipitation data always being present.

(Martin Pihrt) - Water Meter<br/>
Hardened Water Meter I2C/runtime handling. PCF8583 access now uses guarded I2C transactions with a short timeout and fewer retries, the bus is reopened after failures, repeated runtime/I2C errors are throttled, pulse and total settings are clamped before use to avoid division by zero or invalid totals, and JSON status works even when the background thread is not running.

(Martin Pihrt) - Water Consumption Counter<br/>
Hardened Water Consumption Counter settings and event handling. Flow rates, totals, e-mail subject, and selected e-mail plug-in are normalized before use, numeric conversion now safely falls back to zero without traceback spam, repeated signal setup errors are throttled, and master OFF calculations use validated values before updating totals or sending notifications.

(Martin Pihrt) - Voltage and Temperature Monitor<br/>
Hardened Voltage and Temperature Monitor I2C handling. PCF8591 access now uses low-priority guarded I2C transactions with a short timeout, the ADC bus is reopened after failures instead of staying disabled, repeated runtime/I2C errors are throttled, numeric settings are clamped before use, corrupted local JSON logs return empty data, and the settings page can render even when the background thread is not running.

(Martin Pihrt) - Voice Station<br/>
Hardened Voice Station audio playback and file handling. External audio/conversion commands now have timeouts, repeated runtime errors are throttled, ON/OFF station sound indexes and time/volume settings are clamped before use, damaged song queue JSON returns an empty queue, queue length is bounded, sound uploads strip path components and enforce mp3/wav plus a maximum file size, and delete/test actions validate selected indexes.

(Martin Pihrt) - Voice Notification<br/>
Hardened Voice Notification playback and file handling. Missing pygame no longer triggers automatic apt installation; the plug-in now logs the fixed apt command instead. Playback waiting no longer busy-spins the CPU, repeated runtime errors are throttled, settings values and station sound indexes are clamped before use, damaged song queue JSON returns an empty queue, queue length is bounded, sound uploads strip path components and enforce mp3/wav plus a maximum file size, and delete/test actions validate selected indexes.

(Martin Pihrt) - Venetian blind<br/>
Reduced Venetian blind background blocking and hardened web actions. Blind status polling now uses a shorter HTTP timeout and a less aggressive refresh interval, repeated runtime errors are throttled, blind indexes and blind count are validated before commands/tests run, invalid or damaged local JSON logs return empty data, log history is bounded, CSV export uses the correct content type, and status JSON works even when the background thread is not running.

(Martin Pihrt) - Usage Statistics<br/>
Hardened Usage Statistics data loading. External statistics are downloaded with a timeout and maximum response size, page opens reuse cached data instead of downloading on every request, repeated download errors are throttled, the status log now records only a short summary instead of every user record, and the page has a CSRF-protected Refresh action.

(Martin Pihrt) - Thermostat<br/>
Hardened Thermostat runtime handling. Check interval and temperature/program settings are clamped before use, repeated runtime errors are throttled, missing temperature/setup warnings are logged only on state change instead of every cycle, temperature read failures no longer write debug tracebacks repeatedly, and stopping a thermostat program no longer treats unrelated manual runs on the same stations as thermostat-owned runs.

(Martin Pihrt) - Temperature Switch<br/>
Reduced Temperature Switch background load and made output control safer. DS18B20 values from Air Temperature and Humidity Monitor are refreshed at a fixed interval instead of every loop, repeated runtime/probe errors are throttled, numeric settings are clamped before use, duplicate Temperature Switch runs on the same output are avoided, and output OFF now finishes only runs created by this plug-in instead of stopping unrelated scheduler/plugin runs on the same station.

(Martin Pihrt) - Telegram Bot<br/>
Reduced Telegram Bot retry noise and hardened settings input. Repeated connection/runtime errors are throttled, bot token input is stripped of newline characters before saving, and command names are normalized so users can enter them with or without a leading slash.

(Martin Pihrt) - Water Tank Monitor<br/>
Reduced Water Tank Monitor error noise and hardened sensor/log handling. Repeated runtime and I2C read errors are throttled, I2C retry count is lower to avoid long bus blocking, corrupted local JSON log files return empty data instead of repeatedly logging tracebacks, graph timestamp parsing was updated for Python 3, and key numeric settings are clamped before use.

(Martin Pihrt) - System Watchdog<br/>
Hardened System Watchdog status handling. The background checker now refreshes install/service state on every cycle, service state is read via systemctl is-active with a short timeout instead of parsing ps output, repeated status errors are throttled, /etc/modules entries are no longer duplicated, command output decoding is tolerant of invalid bytes, the status page handles a missing checker thread, and the help page now states that Watchdog installation is started explicitly from the button.

(Martin Pihrt) - Speed Monitor<br/>
Reduced Speed Monitor error noise and hardened settings/log handling. Test and log intervals are clamped before use, repeated runtime errors are throttled, corrupted JSON log files return an empty data set instead of crashing the page, graph timestamp parsing was updated for Python 3, and the manual test button now logs the newly measured values instead of the previous status.

(Martin Pihrt) - SMS Modem<br/>
Hardened SMS Modem background handling. The plug-in no longer runs apt installs automatically from its polling thread; missing Gammu dependencies are reported with the fixed apt command instead. Repeated runtime/modem errors are throttled, Gammu config writes use a context manager and report failures cleanly, missing gammu waits longer before retrying, run-now SMS commands validate the program number before use, and settings saving no longer fails when the sender thread is not running.

(Martin Pihrt) - Remote Notifications<br/>
Hardened Remote Notifications event sending. Runtime errors and failed sends are throttled, remote URL/API settings are normalized before use, the API key is hidden with a show/hide button and masked in settings JSON and send logs, successful settings redirects are no longer logged as internal errors, and finished-run handling no longer references the run variable before it exists.

(Martin Pihrt) - Remote FTP Control<br/>
Updated Remote FTP Control for Python 3 and safer FTP operation. Legacy file() calls were replaced with context-managed open() calls, FTP connections now use a timeout and are closed reliably, repeated FTP/runtime errors are throttled, remote path/user/server settings are normalized before use, the FTP password field is hidden with a show/hide button, settings JSON masks the password, and successful settings redirects are no longer logged as internal errors.

(Martin Pihrt) - Direct 16 Relay Outputs<br/>
Hardened Direct 16 Relay Outputs runtime handling. Relay count and trigger level are normalized before use, unsupported platforms now stop GPIO processing cleanly instead of retrying every loop, station-to-relay access is bounded to the configured GPIO list, loop sleeping now responds promptly to plug-in stop, and repeated runtime errors are throttled.

(Martin Pihrt) - Relay Test<br/>
Hardened Relay Test execution. The relay pulse now runs in a short background thread instead of blocking the web request, the relay output is always forced off in a finally block, repeated starts are ignored while a test is already running, stop() also forces the relay off, and the redirect no longer gets logged as an internal error.

(Martin Pihrt) - Pulse Output Test<br/>
Hardened Pulse Output Test runtime handling. Test output and duration are clamped before use, the duration field now exposes the allowed range, the pulse loop can stop promptly through the thread stop event, and the selected output is forced back to a safe state unless an existing scheduler run still needs it active.

(Martin Pihrt) - Proto<br/>
Reduced Proto example background load. The demonstration loop now runs at a lighter interval, status messages are logged only periodically instead of every loop, repeated traceback logging is throttled, and the event window is no longer cleared repeatedly while the plug-in is running.

(Martin Pihrt) - Pressurizer<br/>
Hardened Pressurizer station selection and relay shutdown. Selected station IDs are normalized before schedule matching and rendered correctly after saving, disabled/scheduler-off messages and runtime errors are throttled, missing master-station warnings are logged once per condition, and stopping the plug-in forces the pressurizer relay signal/output off.

(Martin Pihrt) - Pressure Monitor<br/>
Reduced Pressure Monitor load and log spam. The pressure countdown is logged at a throttled interval, the web pressure polling interval is less aggressive, repeated GPIO/runtime/log/SQL/e-mail errors are throttled, selected station IDs are normalized before stopping scheduler runs, GPIO read failures return a safe inactive state, and settings render safely when the background thread is unavailable.

(Martin Pihrt) - Pool Heating<br/>
Reduced Pool Heating background load by refreshing Air Temperature plug-in probe data at a fixed interval and throttling status log rewrites. Repeated runtime/probe/e-mail errors are throttled, settings render safely when the background thread is unavailable, selected output is validated, safety e-mail now respects the Send E-mail switch, and regulation stops only station runs created by this plug-in.

(Martin Pihrt) - Ping Monitor<br/>
Reduced Ping Monitor blocking and log noise. Ping command timeout is shorter, ping and e-mail intervals are clamped to safe minimums, address availability is logged on state changes instead of every cycle, regular ping cycles no longer clear the status log, and repeated runtime/log/CSV/graph errors are throttled.

(Martin Pihrt) - Photovoltaic Boiler<br/>
Reduced Photovoltaic Boiler background load by refreshing Air Temperature plug-in probe data at a fixed interval instead of every loop and by throttling status log rewrites. Repeated runtime/probe errors are now throttled, the settings page works even when the background thread is not available, selected output is validated, and stopping the plug-in only deactivates a station run created by this plug-in.

(Martin Pihrt) - OSPy package Backup<br/>
Hardened backup file handling. Backup creation now prepares missing data/temp/archive folders before creating the zip, the Backup now action includes a CSRF token, and delete/download requests validate the selected backup index and resolved file path before touching files.

(Martin Pihrt) - Network Ping Monitor<br/>
Reduced Network Ping Monitor log and retry noise. Disabled monitoring now writes its status only once instead of every loop, summary and log intervals are clamped to safe minimums, repeated runtime/local-log/SQL-log errors are throttled, and server definitions are rebuilt immediately after saving settings even when the background thread is not currently running.

(Martin Pihrt) - Home Assistant<br/>
Hardened MQTT Home Assistant broker handling. Broker connection attempts now use a shorter timeout and reconnect backoff, publish failures and repeated loop errors are throttled, MQTT payload decoding is tolerant of invalid UTF-8, stopping the plug-in handles missing discovery devices cleanly, settings JSON masks the broker password, and dependency hints now use fixed apt packages instead of pip.

(Martin Pihrt) - MQTT<br/>
Hardened the base MQTT plug-in. Missing paho-mqtt no longer triggers an automatic pip install; settings now show an Install libraries button that installs the fixed apt package python3-paho-mqtt. MQTT broker connection attempts use a shorter timeout and reconnect backoff, publish failures and repeated errors are throttled, the client is stopped more cleanly, the settings JSON output no longer exposes the broker password, and the password field can now be shown or hidden from the settings page.

(Martin Pihrt) - Modbus Stations<br/>
Reduced Modbus Stations blocking during RS485/USB failures by using shorter serial timeouts, throttled serial error logging and a shared serial write lock. The command log is now bounded to the latest entries, missing log files no longer create traceback noise, and address/firmware reads handle short responses without crashing.

(Martin Pihrt) - E-mail Reader<br/>
Added IMAP connection timeouts, a minimum mail check interval, safer logout handling and throttled error logging. Missing sender/folder results now return an empty message list instead of causing follow-up loop errors, reducing load and log spam when the mail server or account settings are unavailable.

(Martin Pihrt) - E-mail Notifications<br/>
Added an SMTP connection timeout and reduced retry load when the mail server is unavailable. The unsent e-mail queue now backs off repeated failed sends instead of retrying at a fixed short interval, and SMTP connections are closed reliably after send attempts.

(Martin Pihrt) - Door Opening<br/>
Audited Door Opening. The plug-in does not run a background loop; opening is started only from the web form. Added validation for selected output and open time, prevented duplicate Door Opening runs on the same output, refreshed footer data after settings changes, and cleared the one-shot sender thread after it finishes.

(Martin Pihrt) - System Information<br/>
Verified that System Information does not run a background thread. Reduced page-open I2C load by scanning the bus once at low priority and reusing the detected address list for plug-in hardware hints instead of probing the same addresses repeatedly.

(Martin Pihrt) - Weather-based Water Level<br/>
Reduced Weather-based Water Level recalculation load by separating normal weather callbacks from forced settings updates. Weather callbacks no longer trigger a full recalculation more often than the hourly calculation interval, calculation errors retry with backoff and throttled logging, and freeze protection now skips cleanly when current temperature data is unavailable.

(Martin Pihrt) - UPS Monitor<br/>
Reduced UPS Monitor status/log load during power failures. The live shutdown countdown is now returned through the JSON status used by the settings page, while the plug-in log is updated only on countdown milestones instead of every loop. The power-restored notification is sent only after a real previous fault.

(Martin Pihrt) - Astro Sunrise and Sunset<br/>
Reduced Astro Sunrise and Sunset background load by calculating sunrise/sunset less often while keeping the one-second program start check. Astral import/calculation errors are now logged with throttling, failed calculations back off before retrying, and the plug-in no longer attempts an automatic pip install on externally managed Python systems.
Added an Install libraries button when Astral is missing. The button installs the fixed apt package python3-astral and writes progress and fallback commands to the status log.

(Martin Pihrt) - Database Connector<br/>
Added a database connection timeout, current settings are now used for each connection attempt, and database cursors/connections are closed reliably after queries. Repeated database errors and routine SQL command logging are throttled so unavailable database servers do not repeatedly block or flood the plug-in log. Database backups now pass a mysqldump connect timeout and report backup timeouts cleanly.

(Martin Pihrt) - E-mail Notifications SSL<br/>
Added an SMTP connection timeout and reduced unnecessary retry load when the mail server is unavailable. The unsent e-mail queue now backs off repeated failed sends instead of retrying at a fixed short interval, and the background loop checks less aggressively while still reacting to finished runs and queued mail.

(Martin Pihrt) - Real Time and NTP time, Air Temperature and Humidity Monitor<br/>
Set Real Time RTC DS1307 I2C access to low priority and Air Temperature DS18B20 I2C reads to normal priority. This keeps time synchronization behind measurement-critical I2C traffic while temperature reads still run ahead of low-priority display updates, with compatibility for older OSPy versions that do not support explicit I2C priorities.
Shortened Real Time NTP request timeout and handled NTP network failures without traceback spam. Air Temperature DS18B20 failures now use a short backoff, fewer failed read attempts and throttled status logging, so a bad sensor or busy I2C bus does not repeatedly block the plug-in loop.

(Martin Pihrt) - Button Control<br/>
Reduced Button Control I2C load by updating MCP23017 LED outputs only when the button state changes. Button input configuration/read transactions now explicitly use normal I2C priority, keeping button presses ahead of low-priority display traffic without pre-empting high-priority wind measurements.

(Martin Pihrt) - Current Loop Tanks Monitor<br/>
Reduced Current Loop Tanks Monitor load by adding a configurable tank measurement interval and reading only tanks that are enabled or required by regulation, stop-station or e-mail rules. Status logging is now throttled so unchanged measurement state is not rewritten every cycle, and repeated browser console debug output was removed from live tank updates.

(Martin Pihrt) - CHMI<br/>
Reduced unnecessary CHMI load during radar service/network failures: failed downloads or bitmap processing errors now wait for the normal 10-minute update interval instead of retrying almost immediately. Radar HTTP requests now reuse one session for downloads and hardware map posts.

(Martin Pihrt) - Shelly Cloud Integration<br/>
Reduced unnecessary Shelly Cloud Integrator load by reusing one HTTP session for device requests, throttling repeated status log writes, adding per-device retry backoff after HTTP/request errors, and handling bad JSON responses without raising an undefined exception. The status window now keeps only the latest written status block instead of accumulating repeated history entries.

(Martin Pihrt) - LCD Display<br/>
Changed LCD Display logging for normal low-priority I2C contention: when the bus is busy, the plug-in now logs a short throttled warning and retries later instead of filling the log with repeated tracebacks. The busy-bus detection now accepts OSError/IOError messages containing `I2C bus is busy`, so small platform differences do not fall back to traceback logging.

July 07 2026
-----------
(Martin Pihrt) - IP Cam<br/>
Refine IP Cam snapshot setup flow.

(Martin Pihrt) - LCD Display<br/>
Added a Wind Speed display switch that shows current and maximum wind speed from Wind Speed Monitor, and re-initializes the HD44780/PCF8574 LCD at the start of each display cycle without re-scanning the I2C address to recover from corrupted characters during long operation.

July 06 2026
-----------
(Martin Pihrt) - IP Cam<br/>
Changed IP Cam snapshot previews to embed cached JPG/GIF files directly in the Snapshots page instead of issuing separate preview requests, avoiding 404 preview errors, and changed the main IP Cam status image size display from bytes to KB.

(Martin Pihrt) - Label Maker<br/>
Updated Label Maker help and README dependency text after the built-in EAN13 barcode generator change. The documentation now separates QR, QR with logo and EAN13 requirements and notes that python-barcode is no longer needed. Added advanced QR settings for module size, border, error correction, foreground/background color, a configurable PNG download filename, clearer preview/download controls, and client/server-side input validation.
Stopped automatic pip installs for missing Label Maker dependencies on externally managed Python environments. The plug-in now logs apt package hints and no longer reports the normal POST redirect as an error. Added an Install libraries button to the Label Maker settings page when required system packages are missing, with installation progress shown in the status log. Replaced the EAN13 python-barcode dependency with an internal EAN13 PNG generator using Pillow, avoiding the unavailable python3-barcode package on Raspberry Pi OS Bookworm.

(Martin Pihrt) - IP Scanner<br/>
Changed the common web ports option from a checkbox to a switch-style control. Improved IP Scanner with active local network discovery, network summary, structured device table, hostname and vendor hints, Gateway/This OSPy/Sensor candidate notes, and optional checks for common web ports 80, 443, 8080 and 8081.

(Martin Pihrt) - Weather-based Water Level<br/>
Added a Forecast details page that shows the last weather calculation input and result, including history, today and forecast rows with rainfall, average temperature, wind, humidity and the resulting water level adjustment.

(Martin Pihrt) - Signaling Examples<br/>
Updated the Signaling Examples plug-in to use a single complete signal list shared by code, settings, help, and README documentation. The settings page now refreshes status automatically and shows the last received signal in a separate auto-updating field.

(Martin Pihrt) - LCD Display, Wind Speed Monitor<br/>
Improved I2C bus cooperation between LCD Display and Wind Speed Monitor: Wind Speed Monitor now requests high-priority I2C access for PCF8583 counter setup and reads, while LCD Display uses low-priority short-timeout access so display scrolling does not delay time-sensitive measurements.
LCD Display now uses HD44780 display-shift commands for scrollable text that fits into the controller DDRAM buffer, reducing I2C traffic while preserving full long-text scrolling behavior for longer messages.
