# OSPy-plugins Changelog

July 19 2026
-----------
(Martin Pihrt) - System Update v1.2.1<br/>
Fixed a stale Diagnostics warning after a successful OSPy update. A valid watchdog acknowledgement now immediately takes precedence over the pending state file, so System Update reports success even if the external watchdog has not yet removed its temporary files. After confirming the scheduler and web interface, the plug-in also records the successful result and removes its own pending marker while leaving the acknowledgement for the external helper. The acknowledgement is accepted only when its token matches the pending update.

July 18 2026
-----------
(Martin Pihrt) - System Update v1.2.0<br/>
Added an external update watchdog that is armed before tracked OSPy files are changed. On systemd installations it runs in an independent transient service and survives the OSPy restart; other systems use a detached helper process. The new OSPy process confirms the update only after a fresh scheduler heartbeat and a listening web interface. If confirmation is not received within 120 seconds, the watchdog resets the repository to the previous commit and branch and restarts OSPy automatically. A watchdog startup failure aborts the update before the working tree is changed, update failures immediately restore the previous revision, and manual rollback commit identifiers are now validated. Diagnostics reports watchdog state and the plug-in help and README describe the recovery process.

(Martin Pihrt) - Automated plug-in tests<br/>
Added GitHub Actions checks for pushes and pull requests to the plug-in `beta` and `master` branches. Each tested plug-in revision now runs the OSPy test suite on Python 3.11 against both OSPy `master` and OSPy `beta`, so stable compatibility and upcoming core changes are verified before promotion. Documented the stable and test branch workflow.

(Martin Pihrt) - SQL logging plug-in dependencies<br/>
Declared Database Connector as an optional ordering dependency for Air Temperature and Humidity Monitor, Current Loop Tanks Monitor, Network Ping Monitor, Pressure Monitor, Tank Monitor, UPS Monitor and Wind Speed Monitor. With both plug-ins enabled, OSPy now starts Database Connector first and stops it last, while every monitor remains usable without SQL logging. Raised the seven affected manifest versions from `1.0.1` to `1.0.2`.

July 17 2026
-----------
(Martin Pihrt) - System Update v1.1.0<br/>
Added explicit update channels. Stable is the default and follows the tested `master` branch; Test follows the fixed `beta` branch and receives changes immediately. Repository checks, manual and automatic updates, status, Diagnostics, e-mail and event records identify the selected channel. Switching from beta back to Stable explicitly installs `master`, even when its revision count is lower. Every update now requires a verified OSPy system safety backup before Git changes are applied, and Git command failures abort the update. Updated the plug-in help.

(Martin Pihrt) - Database Connector and SQL logging plug-ins<br/>
Added a validated table-existence query and changed Air Temperature and Humidity Monitor, Current Loop Tanks Monitor, Network Ping Monitor, Pressure Monitor, Tank Monitor, UPS Monitor and Wind Speed Monitor to create their SQL tables only when missing. Database Connector also no longer reports the harmless MySQL table-exists warning as an error if a concurrent `CREATE TABLE IF NOT EXISTS` reaches the server; genuine table-exists errors from ordinary `CREATE TABLE` statements remain visible.

Raised all eight affected plug-in manifest versions from `1.0.0` to `1.0.1`. Code changes to a released plug-in must include an appropriate semantic-version increment; backward-compatible fixes use the patch component.

(Martin Pihrt) - Database Connector v1.0.2<br/>
Removed obsolete `sender` checks left in the settings and backup pages after the plug-in lifecycle migration. Test connection, connector installation, database backup, file deletion and download actions now use the running plug-in directly without raising `NameError`.

July 16 2026
-----------
(Martin Pihrt) - System Update<br/>
Updated System Update for the new OSPy plug-in interfaces. It now includes a `plugin.json` manifest declaring repository-network, Git subprocess, OSPy-file, restart and e-mail access, registers its periodic checker and manual refresh worker with the shared runtime, observes bounded shutdown and clears its footer, and reports current version and commit, upstream branch, checks, update availability, updates, rollbacks, e-mail and errors through `health()`. The existing update and rollback workflow itself remains unchanged for later hardening.

(Martin Pihrt) - Wind Speed Monitor<br/>
Updated Wind Speed Monitor for the new OSPy plug-in interfaces. It now includes a `plugin.json` manifest declaring SMBus, Raspberry Pi I²C addresses 0x50/0x51, local/SQL logging, e-mail and scheduler/program-control access, registers its monitor with the shared runtime, reuses one SMBus handle instead of leaking a new handle each cycle, interrupts the ten-second measurement and closes I²C during bounded shutdown, clears its footer, and reports worker, counter, speed, maximum, actions, e-mail and errors through `health()`.

(Martin Pihrt) - Weather Stations<br/>
Updated Weather Stations for the new OSPy plug-in interfaces. It now includes a `plugin.json` manifest declaring OSPy sensor, plug-in reading and local settings access, registers its service with the shared runtime instead of leaving a completed thread behind, observes bounded shutdown, and reports display mode, configured channels, sensor count, latest refresh and unavailable values through `health()`.

(Martin Pihrt) - Weather Dashboard<br/>
Updated Weather Dashboard for the new OSPy plug-in interfaces. It now includes a `plugin.json` manifest declaring OSPy sensor, plug-in reading and local settings access, registers its service with the shared runtime instead of leaving a completed thread behind, observes bounded shutdown, and reports mode, configured gauges, latest refresh and unavailable values through `health()`.

(Martin Pihrt) - Weather-based Water Level Netatmo<br/>
Updated Weather-based Water Level Netatmo for the new OSPy plug-in interfaces. It now includes a `plugin.json` manifest declaring OSPy weather, Netatmo-network and irrigation-adjustment access, registers its calculation worker with the shared runtime, closes Netatmo HTTP responses, removes its callback and adjustment during bounded shutdown, applies the final Netatmo-aware adjustment instead of the earlier weather-only intermediate value, keeps credentials out of diagnostics, and reports rainfall, days, adjustment and errors through `health()`.

(Martin Pihrt) - Weather-based Water Level<br/>
Updated Weather-based Water Level for the new OSPy plug-in interfaces. It now includes a `plugin.json` manifest declaring OSPy weather-network, irrigation-adjustment and freeze-protection access, registers its calculation worker with the shared runtime, removes its weather callback, footer and adjustment during bounded shutdown, and reports days, rainfall, water need, adjustment, freeze protection, latest calculation and errors through `health()`.

(Martin Pihrt) - Weather-based Rain Delay<br/>
Updated Weather-based Rain Delay for the new OSPy plug-in interfaces. It now includes a `plugin.json` manifest declaring OSPy weather, Netatmo-network and rain-delay control access, registers its monitor with the shared runtime, closes Netatmo HTTP responses, removes its own rain block during bounded shutdown, keeps credentials out of diagnostics, and reports source, checks, rain detection, active delay and errors through `health()`.

(Martin Pihrt) - Water Meter<br/>
Updated Water Meter for the new OSPy plug-in interfaces. It now includes a `plugin.json` manifest declaring SMBus, Raspberry Pi I²C addresses 0x50/0x51 and local settings access, registers its PCF8583 worker with the shared runtime, closes the I²C handle after errors and during bounded shutdown, and reports worker, counter, address, flow, total, latest reading and errors through `health()`.

(Martin Pihrt) - Water Consumption Counter<br/>
Updated Water Consumption Counter for the new OSPy plug-in interfaces. It now includes a `plugin.json` manifest declaring station-event, local settings and e-mail access, registers its signal listener with the shared runtime, keeps the listener alive and disconnects all master-station signals during bounded shutdown, and reports counters, reset, latest master event, e-mail and errors through `health()`.

(Martin Pihrt) - Voltage and Temperature Monitor<br/>
Updated Voltage and Temperature Monitor for the new OSPy plug-in interfaces. It now includes a `plugin.json` manifest declaring SMBus, Raspberry Pi I²C address 0x48 and local log-file access, registers its PCF8591 worker with the shared runtime, closes the I²C handle after errors and during bounded shutdown, and reports worker, converter, channels, latest reading and errors through `health()`.

(Martin Pihrt) - Voice Station<br/>
Updated Voice Station for the new OSPy plug-in interfaces. It now includes a `plugin.json` manifest declaring audio-output, local sound-file and subprocess access, registers its playback worker with the shared runtime, disconnects station signals and terminates active audio commands during bounded shutdown, and reports worker, queue, playback, station-event and error state through `health()`.

(Martin Pihrt) - Voice Notification<br/>
Updated Voice Notification for the new OSPy plug-in interfaces. It now includes a `plugin.json` manifest declaring optional Pygame, audio-output, local sound-file and mixer-command access, registers its playback worker with the shared runtime, stops active playback during bounded shutdown, and reports worker, Pygame, sound queue, latest cycle, playback and errors through `health()`.

(Martin Pihrt) - Venetian Blind<br/>
Updated Venetian Blind for the new OSPy plug-in interfaces. It now includes a `plugin.json` manifest declaring blind REST-network and local command-log access, registers its status worker with the shared runtime, closes all HTTP responses, observes the common stop request with bounded shutdown, and reports worker, configured and reachable blinds, latest status update, command and errors through `health()`.

(Martin Pihrt) - UPS Monitor<br/>
Updated UPS Monitor for the new OSPy plug-in interfaces. It now includes a `plugin.json` manifest declaring RPi.GPIO, Raspberry Pi physical pins 16 and 18, local/SQL logging, e-mail and system-shutdown access, registers its power worker with the shared runtime, observes the common stop request with bounded shutdown, returns the UPS shutdown output low during stop, and reports worker, power input, shutdown countdown and delay, latest check and errors through `health()`.

(Martin Pihrt) - Thermostat<br/>
Updated Thermostat for the new OSPy plug-in interfaces. It now includes a `plugin.json` manifest declaring temperature-source and program/station-control access, registers its control worker with the shared runtime, observes the common stop request with bounded shutdown, preserves the ownership-safe existing program-control behavior, and reports worker, enabled zones, current temperatures, unavailable sources or setup errors, active program actions, latest cycle and errors through `health()`.

(Martin Pihrt) - Temperature Switch<br/>
Updated Temperature Switch for the new OSPy plug-in interfaces. It now includes a `plugin.json` manifest declaring temperature-source and station-control requirements, registers its regulation worker with the shared runtime, observes the common stop request with bounded shutdown, releases only its own A/B/C station runs during stop, and reports worker, enabled channels, source availability, configured probes, valid readings, active runs and errors through `health()`.

(Martin Pihrt) - Telegram Bot<br/>
Updated Telegram Bot for the new OSPy plug-in interfaces. It now includes a `plugin.json` manifest declaring Telegram network and scheduler/station-control access, registers its asynchronous polling worker with the shared runtime, manages and disconnects its zone-change receiver, observes the common stop request with bounded shutdown, keeps tokens and chat identifiers out of diagnostics, and reports worker, token presence, connection, username, subscribed count, polling, received messages and errors through `health()`.

(Martin Pihrt) - Water Tank Monitor<br/>
Updated Water Tank Monitor for the new OSPy plug-in interfaces. It now includes a `plugin.json` manifest declaring SMBus, Raspberry Pi I²C, local/SQL logging, e-mail and scheduler/station-control access, registers its sensor worker with the shared runtime, closes the SMBus handle after every reading, observes the common stop request with bounded shutdown, releases tank-regulation runs during stop, and reports worker, I²C address, level, fill, distance, volume, regulation, watering block, latest reading and errors through `health()`.

(Martin Pihrt) - System Watchdog<br/>
Updated System Watchdog for the new OSPy plug-in interfaces. It now includes a `plugin.json` manifest declaring Raspberry Pi hardware-watchdog, package-network, system-file, subprocess and service-control access, registers its service monitor with the shared runtime, observes the common stop request with bounded shutdown, and reports worker, package, service, watchdog device, latest check and errors through `health()`.

(Martin Pihrt) - Astro Sunrise and Sunset<br/>
Updated Astro Sunrise and Sunset for the new OSPy plug-in interfaces. It now includes a `plugin.json` manifest declaring optional Astral and pytz plus dependency-installation and scheduler-control access, registers both its calculation and dependency-installation workers with the shared runtime, observes the common stop request with bounded shutdown, and reports worker, Astral availability, location, sunrise, sunset, scheduled programs, dependency installation, latest calculation and errors through `health()`.

(Martin Pihrt) - Speed Monitor<br/>
Updated Speed Monitor for the new OSPy plug-in interfaces. It now includes a `plugin.json` manifest declaring speed-test network and local log-file access, registers its monitoring worker with the shared runtime, removes the unprotected speed test that previously ran before the worker loop, observes the common stop request with bounded shutdown, and reports worker, active test, ping, download, upload, latest successful test and errors through `health()`.

(Martin Pihrt) - SMS Modem<br/>
Updated SMS Modem for the new OSPy plug-in interfaces. It now includes a `plugin.json` manifest declaring Python Gammu, serial-modem, configuration-file, e-mail and system-control requirements, registers its polling worker with the shared runtime, observes the common stop request with bounded shutdown, corrects the webcam e-mail attachment call, keeps administrator telephone numbers out of diagnostics, and reports worker, Gammu, modem, administrator count, signal, latest check, command and errors through `health()`.

(Martin Pihrt) - Shelly Cloud Integration<br/>
Updated Shelly Cloud Integration for the new OSPy plug-in interfaces. It now includes a `plugin.json` manifest declaring Requests and cloud/local network access, registers its polling worker with the shared runtime, closes each HTTP response and its session before bounded shutdown, excludes the cloud authorization key from diagnostics and the settings JSON endpoint, and reports worker, server, configured, loaded and online devices, retry state, latest request and errors through `health()`.

(Martin Pihrt) - Remote Notifications<br/>
Updated Remote Notifications for the new OSPy plug-in interfaces. It now includes a `plugin.json` manifest declaring HTTP network and system-state access, registers its event-monitoring worker with the shared runtime, observes the common stop request with bounded shutdown, closes HTTP responses, keeps the API key out of diagnostics, and reports worker, server, API-key presence, latest cycle, successful notification, reply and errors through `health()`.

(Martin Pihrt) - Remote FTP Control<br/>
Updated Remote FTP Control for the new OSPy plug-in interfaces. It now includes a `plugin.json` manifest declaring FTP network, ramdisk/file and scheduler-control access, registers its polling worker with the shared runtime, closes an active FTP connection before bounded shutdown, keeps credentials out of diagnostics, and reports worker, server, directory, connection, latest command, successful transfer and errors through `health()`.

(Martin Pihrt) - Direct 16 Relay Outputs<br/>
Updated Direct 16 Relay Outputs for the new OSPy plug-in interfaces. It now includes a `plugin.json` manifest declaring RPi.GPIO, Raspberry Pi and all sixteen physical header pins, registers its output worker with the shared runtime, observes the common stop request with bounded shutdown, drives configured outputs to their inactive level during stop, and reports worker, configured and active relays, GPIO readiness, trigger level and errors through `health()`.

(Martin Pihrt) - Real Time and NTP time<br/>
Updated Real Time and NTP time for the new OSPy plug-in interfaces. It now includes a `plugin.json` manifest declaring SMBus, Raspberry Pi I²C address 0x68, NTP network and system-time subprocess access, registers its hourly synchronization worker with the shared runtime, observes the common stop request with bounded shutdown, and reports worker, NTP configuration, latest NTP and RTC values, synchronization cycle and errors through `health()`.

(Martin Pihrt) - Proto<br/>
Updated the Proto example for the new OSPy plug-in interfaces. It now includes a minimal `plugin.json` manifest, registers its example worker with the shared runtime, observes the common stop request with bounded shutdown, documents the manifest in the example structure, and demonstrates worker, counter, latest-cycle and error reporting through `health()`.

(Martin Pihrt) - Pressurizer<br/>
Updated Pressurizer for the new OSPy plug-in interfaces. It now includes a `plugin.json` manifest declaring scheduler, station and master-relay control, registers its scheduler worker with the shared runtime, observes the common stop request with bounded shutdown, guarantees relay release during stop, and reports worker, scheduler, master station, selected stations, relay state, latest activation and errors through `health()`.

(Martin Pihrt) - Pressure Monitor<br/>
Updated Pressure Monitor for the new OSPy plug-in interfaces. It now includes a `plugin.json` manifest declaring Raspberry Pi GPIO 18, logging, e-mail and scheduler-control requirements, registers its monitoring worker with the shared runtime, manages and disconnects all five station signal receivers, performs bounded shutdown, and reports worker, configuration, pressure input, master state, latest check, safety shutdown and errors through `health()`.

(Martin Pihrt) - Pool Heating<br/>
Updated Pool Heating for the new OSPy plug-in interfaces. It now includes a `plugin.json` manifest declaring e-mail and scheduler/station-control access, registers its regulation worker with the shared runtime, observes the common stop request with bounded shutdown, safely releases its controlled pool output during stop, and reports worker, regulation, temperatures, selected output, safety shutdown and errors through `health()`.

(Martin Pihrt) - Ping Monitor<br/>
Updated Ping Monitor for the new OSPy plug-in interfaces. It now includes a `plugin.json` manifest declaring ICMP network, log-file, e-mail, subprocess and optional system-restart access, registers its monitoring worker with the shared runtime, replaces its uninterruptible startup delay with the common stop signal, performs bounded shutdown, and reports worker, configuration, latest check, address availability and errors through `health()`.

(Martin Pihrt) - Photovoltaic Boiler<br/>
Updated Photovoltaic Boiler for the new OSPy plug-in interfaces. It now includes a `plugin.json` manifest declaring scheduler and station-control access, registers its regulation worker with the shared runtime, observes the common stop request with bounded shutdown, continues safely releasing its controlled output during stop, and reports worker, regulation, output, temperature, latest control cycle and errors through `health()`.

(Martin Pihrt) - OSPy Backup<br/>
Updated OSPy Backup for the new OSPy plug-in interfaces. It now includes a `plugin.json` manifest declaring plug-in data file access, removes its unnecessary one-shot worker in favor of explicit lifecycle handling, prevents concurrent archive creation, observes the common stop request between copied plug-ins, and reports active operation, latest archive, size, success, cancellation and errors through `health()`.

(Martin Pihrt) - Network Ping Monitor<br/>
Updated Network Ping Monitor for the new OSPy plug-in interfaces. It now includes a `plugin.json` manifest declaring ICMP network, file and system access, registers its polling worker with the shared runtime, propagates the common stop signal between timeout-bounded target checks, performs bounded shutdown, and reports worker, per-target reachability, completed cycles, partial or total outages and internal errors through `health()`.

(Martin Pihrt) - MQTT Home Assistant<br/>
Updated MQTT Home Assistant for the new OSPy plug-in interfaces. It now includes a `plugin.json` manifest declaring Paho MQTT, python-slugify, Blinker, network and system access, registers its update and short balance workers with the shared runtime, uses real MQTT connect/disconnect callbacks, resubscribes registered topics after reconnect, manages discovery receivers as one replaceable lifecycle set to prevent duplicates, performs bounded shutdown, and reports credential-free broker, discovery, subscription, receiver and publish state through `health()`.

(Martin Pihrt) - Monthly Water Level<br/>
Updated Monthly Water Level for the new OSPy plug-in interfaces. It now includes a `plugin.json` manifest declaring scheduler-control access, registers its daily adjustment worker with the shared runtime, uses the common stop signal with bounded shutdown, continues removing its global adjustment during stop, and reports month, configured percentage, applied factor, latest update and errors through `health()`.

(Martin Pihrt) - Modbus Stations<br/>
Updated Modbus Stations for the new OSPy plug-in interfaces. It now includes a `plugin.json` manifest declaring pyserial, Blinker, serial relay hardware, file and system access, replaces its unnecessary one-shot worker with explicit lifecycle management of three station signal receivers, prevents duplicate commands after restart, closes command serial handles, and reports dependency, receiver and communication state through `health()`.

(Martin Pihrt) - Label Maker<br/>
Updated Label Maker for the new OSPy plug-in interfaces. It now includes a `plugin.json` manifest declaring optional Pillow and QR libraries plus file and subprocess access, removes its unnecessary one-shot worker in favor of explicit lifecycle handling, registers the real dependency-installation worker with the shared runtime, and reports selected type, relevant dependencies, generated output and latest generation result through `health()`.

(Martin Pihrt) - IP Scanner<br/>
Updated IP Scanner for the new OSPy plug-in interfaces. It now includes a `plugin.json` manifest declaring local-network and subprocess access, registers its scanning worker with the shared runtime, propagates the common stop signal into queued host scans while retaining command timeouts, performs bounded shutdown, and reports worker, scan, interface, network, device, port-check and error state through `health()`.

(Martin Pihrt) - IP Cam<br/>
Updated IP Cam for the new OSPy plug-in interfaces. It now includes a `plugin.json` manifest declaring Requests, Pillow, network and cache-file access, registers its automatic snapshot worker with the shared runtime, uses the common stop signal with bounded shutdown, closes completed HTTP responses, and aggregates its existing per-camera diagnostics into a credential-free `health()` report.

(Martin Pihrt) - CHMI<br/>
Updated CHMI for the new OSPy plug-in interfaces. It now includes a `plugin.json` manifest declaring Requests, Pillow, optional SHMU libraries, network, file, subprocess and system access, registers both radar and dependency-installation workers with the shared runtime, uses the common stop signal with bounded shutdown, closes its HTTP session, and reports source, location, optional dependencies, radar timestamp, latest successful update and errors through `health()`.

(Martin Pihrt) - E-mail Reader<br/>
Updated E-mail Reader for the new OSPy plug-in interfaces. It now includes a `plugin.json` manifest declaring IMAP network, e-mail, file and system-control access, registers its mailbox polling worker with the shared runtime, uses the common stop signal with bounded shutdown, closes an active IMAP session after worker errors, and reports non-secret configuration, latest mailbox check, message count and recent IMAP errors through `health()`.

(Martin Pihrt) - E-mail Notifications SSL<br/>
Updated E-mail Notifications SSL for the new OSPy plug-in interfaces. It now includes a `plugin.json` manifest declaring Blinker, SMTP SSL, e-mail and queue-file access, registers its notification and retry worker with the shared runtime, uses the common stop signal, manages five system signal receivers through start and stop to prevent duplicate notifications, and reports receiver, SMTP, queue and delivery state through `health()` without exposing credentials or recipients.

(Martin Pihrt) - E-mail Notifications<br/>
Updated E-mail Notifications for the new OSPy plug-in interfaces. It now includes a `plugin.json` manifest declaring SMTP network, e-mail and queue-file access, registers its notification and retry worker with the shared runtime, uses the common stop signal with bounded shutdown, and reports SMTP configuration, queue size, retry mode, latest successful delivery and recent errors through `health()` without exposing credentials or recipients.

(Martin Pihrt) - Database Connector<br/>
Updated Database Connector for the new OSPy plug-in interfaces. It now includes a `plugin.json` manifest declaring MySQL Connector, network, file and subprocess access, replaces its unnecessary one-shot worker with explicit lifecycle handling, and reports enablement, connector availability and version, configured target, and the latest real database operation through `health()`.

(Martin Pihrt) - Current Loop Tanks Monitor<br/>
Updated Current Loop Tanks Monitor for the new OSPy plug-in interfaces. It now includes a `plugin.json` manifest declaring ADS1115 I2C, file, e-mail and system-control access, registers its measurement worker with the shared runtime, uses the common stop signal with bounded shutdown, closes the SMBus handle after measurements, and reports configured tanks, worker, address, latest successful measurement and I2C or ADC errors through `health()`.

(Martin Pihrt) - Air Temperature and Humidity Monitor<br/>
Updated Air Temperature and Humidity Monitor for the new OSPy plug-in interfaces. It now includes a `plugin.json` manifest declaring Raspberry Pi GPIO, optional SMBus and sensor access, registers its polling worker with the shared runtime, uses the common stop signal with bounded shutdown, and reports configured DHT/DS18B20 sensors, worker, latest sample and sensor errors through `health()`.

(Martin Pihrt) - Button Control<br/>
Updated Button Control for the new OSPy plug-in interfaces. It now includes a `plugin.json` manifest declaring MCP23017 I2C and system-control requirements, registers its polling worker with the shared runtime, uses the common stop signal with bounded shutdown, closes I2C bus handles after operations, and reports enablement, worker, address, successful reads and communication errors through `health()`.

(Martin Pihrt) - CLI Control<br/>
Updated CLI Control for the new OSPy plug-in interfaces. It now includes a `plugin.json` manifest declaring Blinker, file, network, subprocess and system access, removes the unnecessary one-shot startup thread, registers station receivers directly, disconnects them during shutdown, tracks command outcomes, and reports enablement, receiver count, configured commands and the latest result through `health()`.

(Martin Pihrt) - Usage Statistics<br/>
Updated Usage Statistics for the new OSPy plug-in interfaces. It now includes a `plugin.json` manifest declaring file and network access, registers its hourly refresh worker with the shared runtime, uses the common stop signal with bounded shutdown, and reports worker, source URL, record count and latest successful data refresh through `health()`.

(Martin Pihrt) - Signaling Examples<br/>
Updated Signaling Examples for the new OSPy plug-in interfaces. It now includes a `plugin.json` manifest declaring its Blinker dependency and system event access, removes the unnecessary one-shot startup thread, registers receivers directly during startup, disconnects every receiver during shutdown, and reports receiver count and the latest signal through `health()`.

(Martin Pihrt) - Relay Test<br/>
Updated Relay Test for the new OSPy plug-in interfaces. It now includes a `plugin.json` manifest declaring relay-output control, registers and clears its bounded test worker through the shared runtime, stops without a completion race, forces the relay off during shutdown, and reports worker, relay command and duration through `health()`. Corrected the README test duration to three seconds.

(Martin Pihrt) - Pulse Output Test<br/>
Updated Pulse Output Test for the new OSPy plug-in interfaces. It now includes a `plugin.json` manifest declaring station-output control, registers its test worker with the shared runtime, responds separately to the manual test stop and common plug-in stop signals, clears completed workers, and reports the selected output, duration, worker and output state through `health()`.

(Martin Pihrt) - Door Opening<br/>
Updated Door Opening for the new OSPy plug-in interfaces. It now includes a `plugin.json` manifest declaring station-output control, registers its one-shot activation worker with the shared runtime, observes the common stop request before activating an output, stops safely, and reports selected output, opening time, worker state and active opening runs through `health()`.

(Martin Pihrt) - Webcam Monitor<br/>
Updated Webcam Monitor for the new OSPy plug-in interfaces. It now includes a `plugin.json` manifest declaring its Linux USB-camera, file and subprocess access, provides an explicit lifecycle stop function, and reports capture configuration, camera device, `fswebcam` and snapshot availability through `health()`. Corrected the documentation to state that `fswebcam` must be installed through the system package manager.

(Martin Pihrt) - System Debug Information<br/>
Updated System Debug Information for the new OSPy plug-in interfaces. It now includes a `plugin.json` manifest, declares debug-log file access, provides an explicit lifecycle stop function, and reports debug logging and log-file availability through `health()`.

(Martin Pihrt) - System Information<br/>
Updated System Information for the new OSPy plug-in interfaces. It now includes a `plugin.json` manifest, declares its optional Linux and I2C data sources and permissions, provides an explicit lifecycle stop function, and reports optional system-information source availability through `health()`.

(Martin Pihrt) - MQTT<br/>
Updated MQTT as the first reference plug-in for the new OSPy lifecycle and diagnostics interfaces. It now includes a `plugin.json` manifest, registers its sender startup thread with the shared plug-in runtime, uses the common stop signal, and provides `health()` information for dependency availability, configuration, MQTT client state, broker connection, recent publishing and the last runtime error.

(Martin Pihrt) - LCD Display<br/>
Updated LCD Display for the new OSPy plug-in lifecycle and diagnostics interfaces. It now includes a `plugin.json` manifest declaring its I2C dependency, registers its display thread with the shared runtime, uses the common stop signal, and provides `health()` information for worker state, detected PCF8574 address, successful display writes and recent I2C errors.

(Martin Pihrt) - Documentation<br/>
Updated active pihrt.com links in plug-in README files, help templates, and source comments after the website migration. Former `/elektronika/` article paths now use their verified `/clanky/` addresses, and the removed AutomatOSPy demonstration page now links to the related irrigation article.

July 12 2026
-----------
(Martin Pihrt) - Usage Statistics<br/>
Updated Usage Statistics for the anonymized public data format. The public statistics feed now uses SHA-256 installation identifiers, and the plug-in hashes its local UUID before comparison so it can still recognize and highlight the current installation without publishing the original UUID.

July 11 2026
-----------
(Martin Pihrt) - E-mail Notifications SSL<br/>
Added a small two-factor authentication interface for OSPy. The plug-in can now report whether its SMTP configuration is ready and send time-sensitive login verification codes immediately without placing failed or expired codes into the normal retry queue.

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
