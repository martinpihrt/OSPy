# OSPy-plugins Changelog

August 30 2026
--------------
(Martin Pihrt) - Wind Speed Monitor v1.2.3 and Venetian Blind v1.2.8<br/>
Added an independent Wind Monitor sensor-failure safety program with a configurable consecutive-failure count and separate program selection. The program starts once during a continuous measurement fault and is armed again only after an accepted reading; intentional RS485 bus scans remain neutral pauses. Diagnostics expose the action state, and failed e-mail delivery is distinguished from a successful notification and retried after the reminder interval. Venetian Blind now immediately blocks and clears pending automatic raising and lowering while Wind Monitor is unavailable or faulty, without cancelling the one safety program started directly by Wind Monitor.

August 29 2026
--------------
(Martin Pihrt) - RS485 Communication v1.0.3<br/>
Expanded device discovery with the address 255 broadcast method used by ZTS and compatible sensors, a longer-timeout probe matrix for the likely factory address 1, one- and two-register requests, Modbus functions 03 and 04, addresses 1-254 and 8N1, 8E1 and 8O1 framing. The live page now reports the current scan phase, complete serial and Modbus parameters, transmitted request and latest received frame. The configured serial settings are restored after discovery.

(Martin Pihrt) - Wind Speed Monitor v1.2.2 and RS485 Communication v1.0.2<br/>
Handled a disabled, stopped or unavailable optional RS485 Communication provider as a visible Wind Monitor validation and health error instead of an internal page failure. Fixed fixed-length RS485 transactions treating an empty or partial response as successful communication: missing bytes now produce a timeout error, fail the queue job, preserve transmitted and received byte counters, and expose the real no-response condition in RS485 status and diagnostics. Added a background RS485 bus discovery action that scans Modbus addresses 1-247 at eight common sensor speeds, validates normal and exception response CRCs, pauses ordinary queue traffic during discovery, and reports live progress and all discovered devices. Updated documentation, versions, asset cache keys and regression coverage.

August 26 2026
--------------
(Martin Pihrt) - Venetian Blind v1.2.7<br/>
Changed native mobile blind captions from state adjectives to the Open, Stop and Close command verbs. Automatic opening in strong wind and closing for temperature shading now remain pending until every enabled Shelly confirms the requested end position. An active or queued program is never overlapped; after a minimum 60-second verification delay, an unconfirmed target is retried whenever its safety or shading conditions remain satisfied. Configured tilt captions remain unchanged. Updated documentation and regression coverage.

(Martin Pihrt) - OSPy Backup v1.0.5<br/>
Added stable native mobile metric IDs and marked `last_backup_size` as a byte-sized `data_size` quantity, allowing clients to display a readable B, kB or MB value instead of a raw integer.

August 25 2026
--------------
(Martin Pihrt) - OSPy Backup v1.0.4<br/>
Added native mobile creation and download of the newest plug-in-data ZIP. The manifest declares the guarded `create_backup` action and `latest_backup` download, mobile cards expose only the download currently available, and the download descriptor is restricted to a verified archive inside the plug-in data directory. Concurrent backup protection and the existing provider action remain authoritative. Updated the README, manifest and mobile-interface regression coverage. Downloading requires matching OSPy Mobile API v1 plug-in-download support.

(Martin Pihrt) - System Update v1.2.7<br/>
Replaced position-based mobile metric identifiers with stable language-neutral IDs for enabled state, automatic updates, check state, update availability, current and target commits, stable release, branch, channel and watchdog results. Native clients can now localize and safely bind Check and Install controls without depending on translated labels or metric order. Updated the README, manifest and regression coverage; update execution remains on the scoped core `/updates/actions/check|apply|rollback` endpoints.

(Martin Pihrt) - Venetian Blind v1.2.5<br/>
Exposed open, stop, close and all four configured tilt actions on every enabled mobile blind card. Each action carries the stable blind UID, uses the same validated control path as the web interface and Automation Rules, and displays the administrator's saved tilt label when present. Updated the README, manifest and regression coverage.

August 23 2026
--------------
(Martin Pihrt) - Automation Rules v1.1.3, Venetian Blind v1.2.4, Water Meter v1.2.1, Pressure Monitor v1.1.1, Water Tank Monitor v1.1.1, Current Loop Tanks Monitor v1.1.1 and OSPy Backup v1.0.3<br/>
Added concrete provider actions for opening, stopping, closing or tilting one Venetian blind, safely stopping ultrasonic or current-loop tank regulation, resetting the ultrasonic tank's recorded minimum and maximum, and creating a plug-in data backup. Automation Rules displays localized action names and uses only actions declared by running providers. Existing mobile blind control, tank regulation cleanup and guarded backup implementations are reused. Updated manifests, help, READMEs and regression coverage.

(Martin Pihrt) - Automation Rules v1.1.2 and Water Meter v1.2.1<br/>
Added bounded action-history records for every output-cycle start, pause, resumed run, failure and final stop, including the stop reason. Water Meter now declares and implements the first concrete external provider action, allowing an explicitly configured live Automation Rules rule to reset its total, current-minute and current-hour consumption counters through OSPy's validated provider-action entry point. Updated help, READMEs, manifests and regression coverage.

(Martin Pihrt) - Venetian Blind v1.2.3<br/>
Changed temperature shading to arm only on a confirmed transition of every enabled blind to fully open. One lowering action consumes the armed state, so manually tilting or partially moving a blind afterward no longer causes repeated closing while temperature remains high; a later full opening by strong-wind protection or by the user rearms the next cycle. Changed Mobile API status `updated` from a raw Unix timestamp to the same `YYYY-MM-DD HH:MM:SS` text used by other plug-ins. Updated help, READMEs, cache versions and regression coverage.

(Martin Pihrt) - Venetian Blind v1.2.2<br/>
Fixed complete blind records being discarded after an OSPy restart, update or live plug-in reload because the saved list did not match the `None` default type. The complete Gen1/Gen2/Custom configuration is now stored only as a structured list in OSPy `PluginOptions`; old parallel settings and migration paths were removed, and the plug-in creates no configuration JSON file. Profiles, hosts, labels and all tilt positions, labels and URLs now persist. Fixed the automation queue remaining blocked by OSPy's completed Run-Now object after its first raising or lowering program, so temperature shading and strong-wind protection can alternate repeatedly without restarting OSPy. Added a native Mobile API v1 status card for every configured blind with state, position, connection and profile data, plus declared open, stop, close and tilt actions for clients that support manual card controls. Updated both READMEs, the manifest and regression coverage.

August 22 2026
--------------
(Martin Pihrt) - Automation Rules v1.1.1<br/>
Added a bounded cyclic mode to the output-on action with configurable run duration, off pause and maximum total cycling time. Cycles continue only while all required rule data remains available and the rule still matches; disabling the rule, automation, control actions or manual mode, editing or deleting the rule, stopping the plug-in, losing a condition or reaching the limit cancels the cycle and switches its output off. Cycles are not resumed after restart and one output cannot be owned by multiple cycles. Corrected the minimum compatible OSPy version from 3.0.348 to 3.0.354 and replaced the ineffective `min_version` manifest key with the supported `min` key, so OSPy must be updated before installing this Automation Rules release. Updated help, READMEs, diagnostics, cache versions and regression coverage.

(Martin Pihrt) - Automation Rules v1.1.0<br/>
Added guarded one-shot control actions for selected stations, all outputs, scheduler disabling, running programs, bounded manual output control, global water-level adjustment and actions explicitly declared by another provider. Control execution is separately disabled by default, test mode simulates actions without touching OSPy or hardware, and every result is recorded without suppressing notifications. Optional incident locking requires administrator acknowledgement and refuses to unlock while conditions remain active or unavailable. Added action state to diagnostics and the mobile rule cards, updated localized help and expanded regression coverage.

(Martin Pihrt) - CHMI v1.0.7<br/>
Fixed manual CHMI rain-delay removal being undone by the next rainy radar evaluation. A manual removal is now persisted for the current rainy period and cleared only after a valid dry radar sample; disabling CHMI rain-delay control immediately removes the CHMI-owned block. The synchronized update path prevents the radar worker from recreating a block concurrently, while manual and other plug-in delays remain untouched. Added visible override status, diagnostics, help, README and regression coverage.

(Martin Pihrt) - UPS Monitor v1.0.5<br/>
Added an enabled-by-default Automatic system shutdown switch. Administrators can now keep power-line monitoring, logging and fault or recovery E-mail notifications active without pulsing the UPS shutdown output or shutting down OSPy. Countdown, health and mobile status text now distinguish automatic shutdown from monitor-only operation, and the help and README describe both modes.

(Martin Pihrt) - Automation Rules v1.0.8<br/>
Collapsed all saved rules and the New rule card on an ordinary page load. Saving an existing or new rule now returns to the same expanded card while every other rule remains collapsed. Added a compact localized header summary of configured conditions, AND/OR matching, limits, units and notification channels, with the complete summary available as hover text and responsive wrapping on narrow screens. Added native mobile API v1 metrics cards that report each rule as Disabled, Ready, Triggered, Conditions active, Unavailable or Automation disabled and expose every individual condition as Active, Inactive, Unavailable or Not evaluated using read-only cached provider values. Updated help, README, asset cache versions and regression coverage.

(Martin Pihrt) - Automation Rules v1.0.7<br/>
Added a built-in read-only OSPy status source for scheduler state, manual and scheduled modes, water-level adjustment, remaining rain delay, rain-sensor configuration and activity, cached OSPy update state, cached plug-in update state and known plug-in update count. The source never starts a network update check. General settings now stay on one readable desktop row, saved rule cards are collapsible, and rule headings distinguish Disabled, Ready and Triggered states with a plain green Triggered indicator. Updated help, READMEs, cache versions and regression coverage.

August 21 2026
--------------
(Martin Pihrt) - Automation Rules v1.0.6<br/>
Changed browser delivery to prefer the standards-based Service Worker notification path used by Firefox, with the direct Notification constructor retained as a fallback. The permission action now explicitly enables and tests notifications, asset cache versions force updated browser code, and delivery failures are displayed on the Automation Rules page instead of being silently discarded. Updated READMEs and regression coverage.

(Martin Pihrt) - Automation Rules v1.0.5<br/>
Added a built-in local Date and time source with ISO date, 24-hour time, weekday, month and day-of-month values. New in-range and outside-range comparisons accept `start..end` and correctly support overnight windows such as `22:00..06:00`, so time windows can be combined with measurements through AND. Trigger, repeat and recovery notifications now state each resource, value, actual reading, operator and configured limit, including structured details for the mobile app. Browser permission now sends an immediate visible test, browser delivery falls back to a Service Worker where the direct Notification API is unavailable, and Home messages preserve multiline details. Updated help, READMEs, asset cache versions and regression coverage.

(Martin Pihrt) - Automation Rules v1.0.4<br/>
Added every enabled built-in OSPy sensor as a read-only Automation Rules source independently of Pihrt or Shelly hardware. The adapter exposes each sensor's configured measurement without another hardware poll; Pihrt multi-contact and soil devices expose individual inputs, while ultrasonic tank sensors provide distance, derived water level, fill percentage and volume. Offline sensors and invalid probe values remain unavailable and cannot satisfy or silently clear a condition. Updated localized help, READMEs and regression coverage.

(Martin Pihrt) - Automation Rules v1.0.3<br/>
Enabled browser-notification polling on every authenticated OSPy page instead of only Home. Home popup cards remain exclusive to Home and are not marked as consumed while another page is open. Mobile push data now includes the stable rule ID, rule name and event so a matching application can localize Automation Rules notifications without parsing server display text. Updated asset cache versions, documentation and regression coverage.

(Martin Pihrt) - Automation Rules v1.0.2<br/>
Kept the general switches directly beside their labels so each control is visually unambiguous. Added a confirmed Test notifications action that ignores conditions and timing, sends one real message through every channel currently selected in the rule even while global test mode is enabled, records individual delivery results and does not alter incident state. Updated the help, README, asset cache versions and regression tests.

(Martin Pihrt) - Automation Rules v1.0.1<br/>
Replaced every visible settings checkbox and notification-channel checkbox with the red and green sliding switch used by other OSPy plug-ins. Added localized hover descriptions to editor fields, selectors, switches and action buttons, and versioned the browser assets so installed systems immediately load the updated interface.

(Martin Pihrt) - Shelly Cloud Integration v1.0.8<br/>
Fixed Shelly 2.5 roller and switch processing referencing an unassigned `a_voltage` variable even though the device response stores its shared voltage as `voltage`, which stopped the complete Integrator polling cycle with `UnboundLocalError`. Corrected the local switch-mode Wi-Fi response path and fixed Shelly 2PM Add-on and Shelly 1PM Add-on status lines so RSSI and update time are placed in their intended fields. Updated the version, cache key, help, READMEs and regression tests.

(Martin Pihrt) - Energy Meter v1.0.6 and Shelly Cloud Integration v1.0.7<br/>
Fixed Energy Meter reporting a configured Shelly meter as unavailable when it started before Shelly Cloud Integration had populated its runtime cache. Shelly Cloud Integration now safely exposes snapshots of configured identities and cached readings even before its worker starts, while Energy Meter also understands the previous parallel-list interface. Energy Meter distinguishes missing, disabled, offline and still-loading devices; a still-loading meter is retried every five seconds without logging a failure traceback, while other successful meters keep their configured sampling interval and Diagnostics reports a waiting state until data arrives. Shelly IDs are matched case-insensitively and labels remain exact. Updated versions, cache keys, help, READMEs and regression tests.

(Martin Pihrt) - Venetian Blind v1.2.1<br/>
Recognized complete standard Shelly Gen1 roller URL sets during both initial and already completed legacy migration, restoring the Shelly Gen1 profile and host instead of displaying them as Custom REST URLs while preserving nonstandard custom configurations unchanged. Test command buttons now return to the editor for the same blind, allowing consecutive command checks without reopening it. Updated the README, cache version and regression tests.

(Martin Pihrt) - Venetian Blind v1.2.0<br/>
Fixed temperature automation reading a nonexistent sensor attribute instead of the actual OSPy `last_read_value` channel, which prevented the lowering program from starting even above the configured limit. Replaced repeated cached-wind sampling with unique accepted Wind Monitor measurements and added a configurable minute window for the required strong-wind exceedances. Removed temperature hysteresis from the active settings because authoritative position checks now control re-entry. Mixed positions such as eight closed blinds and one open blind now start lowering when all environmental conditions are met; strong wind starts raising whenever any enabled blind is not confirmed open, including tilted, intermediate and unreachable devices. Continuous-condition guards prevent relay repetition, active external programs suppress duplicates, strong wind cancels pending lowering, and Diagnostics reports the current temperature, wind confirmation counts and confirmed blind-state count. Updated settings explanations, help, README and regression tests.

August 20 2026
--------------

(Martin Pihrt) - Venetian Blind v1.1.1<br/>
Replaced every visible settings checkbox with the same accessible red and green sliding switch used by other OSPy plug-ins. The change covers individual blind enablement, plug-in control, logging, footer output and temperature and wind automation while preserving all existing form names, saved values and backward compatibility.

(Martin Pihrt) - Shelly Cloud Integration v1.0.6<br/>
Restored local device previews in the add and edit form and added them to both the compact list and responsive card views. Changing the selected device type or generation refreshes the editor preview immediately, and selecting any preview opens the matching current official Shelly Knowledge Base page in a new tab. Reused the complete local image set already stored in the plug-in, corrected Shelly 2.5, Gen1 and Gen2 Plug S, 1 Mini and Add-on mappings, and avoided external image requests from the settings page.

(Martin Pihrt) - Energy Meter v1.0.5<br/>
Added a calendar-day selector to the overview, displayed historically calculated cost and feed-in income for every summary period, and applied the selected day to solar calculations. Fixed equal tariff start and end times to cover the complete selected day, replaced end-of-interval tariff assignment with time-weighted pricing across tariff boundaries, rejected non-finite price values, and exposed the stored import and feed-in prices in the history table. Local JSON, optional SQL and CSV now preserve the tariff, currency, applied unit prices, cost and income for every interval; the history uses the stored currency and overview monetary totals no longer combine records from different currencies. Clarified that calendar days use the OSPy server's local time from 00:00 inclusive to the next 00:00 exclusive without resetting Shelly cumulative counters. The delete-history confirmation, in-app help and README now state explicitly that overview totals are derived from retained interval history and are therefore cleared with it, while the preserved counter baseline only prevents a false spike in the next sample.

(Martin Pihrt) - Wind Speed Monitor v1.2.1<br/>
Added independent technical fault e-mail notifications for PCF8583/I2C setup and read failures, RS485 dependency, queue, serial and protocol failures, rejected implausible measurements and unexpected worker errors. Moved the shared e-mail subject and provider selection into a dedicated E-mail settings section, added a separate error-notification switch and a configurable one-to-168-hour reminder interval, and exposed active incident details through plug-in health diagnostics. The first failure sends immediately, repeated failures are bounded to the reminder interval, and one accepted measurement closes the incident; temporary I2C lock contention and valid zero wind remain non-error states. Updated the in-app help, README, cache version and regression tests.

(Martin Pihrt) - Shelly Cloud Integration v1.0.5<br/>
Replaced sensor-count based configuration with individual Add new Shelly, Edit and confirmed Delete actions. Existing installations retain their device order, enabled state, labels, Shelly IDs, types, generation, reading source, local addresses and add-on labels through a backward-compatible migration that adds stable internal device identifiers. Added a saved List or Cards display choice, responsive external styling, isolated global and per-device forms, immediate cache invalidation for changed or removed device IDs, bounded input normalization, updated help and README documentation, and regression tests.

(Martin Pihrt) - Venetian Blind v1.1.0<br/>
Replaced blind-count configuration with individual Add, Edit and confirmed Delete actions plus saved list or card display. Added backward-compatible migration of all existing labels and REST URLs, Shelly Gen1 roller and Gen2+ Cover RPC profiles, four configurable tilt positions, authoritative position classification and responsive manual controls. Added temperature-sensor shading inside a configurable time window after a required safe-wind sample window, continuous confirmed strong-wind raising through multiple sequentially queued programs, strong-wind priority over pending lowering actions, active-program observation for ESP32 or manual starts, and a state latch that prevents repeated relay commands while a condition remains active. Updated permissions, optional Wind Monitor dependency, help, README and regression coverage.

August 19 2026
--------------
(Martin Pihrt) - RS485 Communication v1.0.1<br/>
Added a central RS485 service plug-in for the Waveshare industrial CH343G USB-to-RS485 adapter. It owns one configurable serial interface, serializes dependent plug-in traffic through a bounded FIFO worker, supports synchronous, asynchronous and atomic multi-step operations, automatically detects the adapter, exposes protected status and health diagnostics, validates manual device paths and communication parameters, and safely tests the adapter without transmitting arbitrary bus data. Added CSRF-protected OSPy-themed settings, responsive local product images and adapter documentation, bounded frame/read/delay handling, the required pyserial dependency, and automated security, queue, manifest, template and validation tests.

August 17 2026
--------------
(Martin Pihrt) - System Update v1.2.6<br/>
Extended the external watchdog confirmation window from two to five minutes. Large installations that initialize many plug-ins sequentially now have enough time to start System Update, produce a fresh scheduler heartbeat and open the web interface before automatic rollback, while the existing commit, token and health checks remain unchanged.

(Martin Pihrt) - Astro Sunrise and Sunset v1.0.6<br/>
Replaced the placeholder Astral region `OSPy` with the region detected from the OSPy weather location. Existing installations fall back to the detected country code until the next weather location lookup stores the more precise region.

(Martin Pihrt) - Astro Sunrise and Sunset v1.0.5<br/>
Added a stable read-only astronomical provider for native OSPy sunrise and sunset program types. The provider reports whether Astral and location calculation are ready and returns validated dawn, sunrise, noon, sunset and dusk datetimes for a requested day without guessing fallback clock times. Existing plug-in scheduling and the mobile daylight interface remain available.

August 14 2026
--------------
(Martin Pihrt) - Weather Dashboard v1.0.2, Astro Sunrise and Sunset v1.0.4 and Wind Speed Monitor v1.1.9<br/>
Added a native Weather Dashboard mobile interface carrying the configured canvas/text mode, live gauge values, scale ticks and colored limits. Replaced Astro's synthetic history series with a fixed 24-hour sunrise/sunset timeline contract so mobile clients can render night/day bands without irrelevant history-range controls. Documented the stable Wind Speed Monitor mobile trend codes used by the Android application and its automatic expanded-panel refresh behavior.

(Martin Pihrt) - Shelly Cloud Integration v1.0.4<br/>
Preserved the full Shelly three-phase cumulative energy-counter precision in the integration cache. Energy Meter interval history no longer consists mostly of zero values followed by artificial 0.001 kWh steps at low power. Added a regression test for sub-Wh counter values.

August 12 2026
--------------
(Martin Pihrt) - Energy Meter v1.0.4<br/>
Expanded the overview into separate energy and power graphs. Energy now shows grid import and export L1/L2/L3/total plus solar production, while power shows L1/L2/L3/total for every configured meter. The history table now also displays phase power, and administrators can permanently clear local, SQL or dual history through a confirmed CSRF-protected action without losing the cumulative-counter baseline. Local interval storage now appends records to `history.jsonl` instead of rewriting the complete `history.json` list every sampling interval; existing JSON history remains readable and bounded retention compacts the journal periodically. Updated help, README and regression tests.

August 9 2026
-------------
(Martin Pihrt) - Energy Meter v1.0.3 and Shelly Cloud Integration v1.0.3<br/>
Added the multi-meter Energy Meter plug-in with direct local Shelly RPC as the recommended source and the Shelly Cloud Integration cache as an optional per-meter source. It supports Grid, Solar production, Load and Auxiliary roles, L1-L3 and total power/energy, separate import and grid export, today/yesterday/month/year totals, solar self-consumption and independence calculations, atomically persisted counter baselines across OSPy restarts, safe meter-reset/replacement handling, weekday/time tariffs with historically fixed prices, costs and feed-in income, local JSON and optional SQL history, CSV export, responsive graphs, Home summary, diagnostics and bounded mobile API data. Shelly three-phase cache payloads now also expose per-phase and total returned-energy counters required for feed-in logging.
Fixed web.py template block indentation so settings, empty history and the overview render completely, kept the OSPy footer outside the history table, and aligned Energy Meter framing and cards with Wind Speed Monitor.
Energy Meter settings now use the standard OSPy switch component for boolean values and localized Monday-through-Sunday push buttons instead of numeric weekday input.
Added the switch CSS used by Air Temperature and Humidity Monitor so all Energy Meter boolean controls render as red/green sliders, and changed both dynamic enabled-column headings to the untranslated literal `Enabled`.

August 8 2026
-------------
(Martin Pihrt) - Shelly Cloud Integration v1.0.2 and Weather Dashboard v1.0.1<br/>
Fixed Shelly Pro 3EM and Shelly 3EM-63T Gen3 processing by using all three phase voltages, correcting the phase power and energy ordering, tolerating devices without an internal-temperature component and normalizing local and cloud status payloads. The Weather Dashboard can now display cached per-phase power, reverse power, voltage, current, power factor and energy plus total power and total energy. Added regression tests for the Shelly 3EM-63T Gen3 payload.

(Martin Pihrt) - OSPy Package Backup v1.0.2<br/>
Restored the latest successful plug-in backup status from existing ZIP archives after OSPy or the plug-in restarts. The native mobile status and diagnostics now report the newest persistent archive name, modification time and size instead of resetting to “no backup created”. Added regression tests for archive discovery.

August 21 2026
--------------
(Martin Pihrt) - Automation Rules v1.0.0, Telegram Bot v1.0.1, E-mail Notifications v1.0.1 and E-mail Notifications SSL v1.1.6<br/>
Added a responsive graphical rule builder over cached `ospy.provider.v1` values. Rules support up to twenty row/card conditions, AND/OR matching, confirmation time, notification repetition, recovery messages, severity, a separate default-on test state, bounded action history and diagnostics. Notification actions include an OSPy Home popup, explicitly permitted browser notifications, e-mail, Telegram and mobile push; provider failures are isolated and cannot clear an active incident. Automation Rules performs no irrigation control actions. Telegram Bot now exposes a bounded external-notification entry point for authorized chats, and both e-mail plug-ins return delivery success to callers without changing existing notification behavior.

(Martin Pihrt) - Water Meter v1.2.0, Pressure Monitor v1.1.0, Water Tank Monitor v1.1.0 and Current Loop Tanks Monitor v1.1.0<br/>
Added the shared read-only `ospy.provider.v1` capability and snapshot interface for Automation Rules and Irrigation Safety. The four adapters expose only cached values, stable identifiers, canonical units and machine-readable alerts, without additional I²C/GPIO operations or changes to their existing workers, pages, health reports and mobile contributions. Added contract and no-hardware-access regression tests.

August 7 2026
-------------
(Martin Pihrt) - Water Meter v1.1.1<br/>
Fixed an enabled Water Meter remaining at zero after PCF8583 initialization or block-read failure. Counter data is now read explicitly as three bytes from registers 0x01-0x03, failed setup closes the bus and is retried automatically, setting changes request safe worker-thread reinitialization, and the overview reports the active I2C error instead of presenting a misleading running state.

(Martin Pihrt) - Water Meter v1.1.0<br/>
Changed the PCF8583 worker to uninterrupted one-second measurement cycles so the live liters-per-second value refreshes every second without discarding pulses during an extra sleep. Added a Wind Monitor-style responsive overview, per-second live refresh, liters-per-minute conversion, current-minute/current-hour/total cards, separate settings and log pages, local JSON and optional SQL logging, selectable graph/log source, seconds-based logging interval, zero-flow filtering, bounded or unlimited record retention, CSV download, and a flow history graph. Added an optional Home value in the format `current l/s (current l/min)` with lifecycle cleanup and mobile API v1 cards plus bounded flow history, declared Database Connector as optional, expanded help and README documentation, and added regression tests.

(Martin Pihrt) - Wind Speed Monitor v1.1.8 and Water Meter v1.0.2<br/>
Changed selectable-I2C settings conflicts from a standalone HTTP 400 error page to an inline red status bar on each plug-in settings page. A rejected submission keeps all preceding settings, remains on the form and exposes the message with alert semantics for assistive technology. Added regression tests and updated the repository, plug-in README and in-app help documentation.

(Martin Pihrt) - Wind Speed Monitor v1.1.7 and Water Meter v1.0.1<br/>
Declared PCF8583 addresses 0x50 and 0x51 as selectable alternatives instead of two simultaneously occupied I2C resources. Both plug-ins can now be installed from the official repository or a custom ZIP and run together on distinct addresses. During activation each plug-in keeps its preferred address when available or selects the free alternative; both settings pages reject an address already used by another enabled plug-in. Updated the repository, plug-in README and in-app help documentation.

August 6 2026
-------------
(Martin Pihrt) - CHMI v1.0.6, E-mail Notifications SSL v1.1.5, LCD Display v1.0.2, Monthly Water Level v1.0.1, Home Assistant MQTT v1.0.1, OSPy Package Backup v1.0.1, System Debug Information v1.0.1, System Update v1.2.5, Thermostat v1.0.1, Usage Statistics v1.0.1 and Weather-based Water Level v1.1.2<br/>
Added safe, read-only Mobile API v1 operating cards for the listed service and system plug-ins without exposing credentials or configuration. CHMI now marks the OSPy weather location on a generated copy of the current radar frame and formats compact radar timestamps as a readable local date and time. Cards without graph data no longer advertise an empty series, allowing native clients to omit irrelevant history controls.

(Martin Pihrt) - Astro Sunrise and Sunset v1.0.3<br/>
Fixed the native mobile card so its sunrise, sunset, twilight, moon phase and 24-hour daylight data are returned instead of being discarded by a datetime namespace error.

(Martin Pihrt) - Air Temperature and Humidity Monitor v1.0.7, CHMI v1.0.5, Real Time and NTP v1.0.1, Shelly Cloud Integrator v1.0.1, Astro Sunrise and Sunset v1.0.2, System Information v1.0.1, UPS Monitor v1.0.4, Water Consumption Counter v1.2.7 and Weather-based Water Level v1.1.1<br/>
Expanded the read-only Mobile API v1 adapters. Shelly Cloud now reports cached device readings, Astro supplies sunrise, sunset, twilight, moon phase and a 24-hour daylight series, Real Time reports recent synchronization state, System Information exposes cached host statistics, and Weather-based Water Level publishes the selected calculation method and its current result. Temperature, CHMI radar, UPS and virtual water-meter mobile data now follow the requested history source and range more accurately, preserve current runtime values, identify both master counters, use cubic metres from 1000 litres and provide the current radar frame with the geographic outline. No mobile adapter performs configuration or initiates a hardware, cloud or database measurement.

July 30 2026
------------
(Martin Pihrt) - Air Temperature and Humidity Monitor v1.0.5, CHMI v1.0.4, Water Consumption Counter v1.2.6 and Wind Speed Monitor v1.1.5<br/>
Refined the native mobile API data. Temperature history now contains only enabled sensors and stable series identifiers. CHMI supplies the latest radar image and a concise local rain state instead of an RGB history chart. Water consumption uses the live master and running-station counters, and wind metrics include stable identifiers for localized values and trend display.

July 29 2026
------------
(Martin Pihrt) - Air Temperature and Humidity Monitor v1.0.4, Wind Speed Monitor v1.1.4, Water Consumption Counter v1.2.5, Current Loop Tanks Monitor v1.0.3, Water Tank Monitor v1.0.3, UPS Monitor v1.0.3 and CHMI v1.0.3<br/>
Added the optional, read-only mobile API v1 contribution to the selected monitoring plug-ins. The Android application can now display each plug-in's current operating state and measurements; temperature, wind, tank and radar plug-ins also expose bounded local history series for native graphs. Mobile reads use existing in-memory values and local history files and never initiate hardware, network or SQL measurements.

(Martin Pihrt) - Wind Speed Monitor v1.1.3<br/>
Stopped the measurement loop from rewriting every normalized plug-in setting on every sample. Values are now persisted only when normalization actually corrects a value, reducing settings-database traffic and avoiding stale settings-object assignments during a live plug-in update.

(Martin Pihrt) - Wind Speed Monitor v1.1.2<br/>
Made every diagnostic and history file path explicitly target the Wind Speed Monitor data directory. Runtime files such as `diagnostic.log.1` can therefore no longer be created at the shared plug-in root and mistaken for an installable plug-in by OSPy.

July 28 2026
------------
(Martin Pihrt) - Wind Speed Monitor v1.1.1<br/>
Restored the point-hover tooltip in the automatically refreshed history graph. Each measured point again shows its time and current value, plus the preceding value when available. Tooltip handlers and data are rebuilt safely after every background graph refresh, point order is normalized chronologically, and the tooltip styling is kept in the plug-in CSS.

August 5 2026
-------------
(Martin Pihrt) - Air Temperature and Humidity Monitor v1.0.6, Wind Speed Monitor v1.1.6, Water Tank Monitor v1.0.4 and Current Loop Tanks Monitor v1.0.4<br/>
Extended the native mobile chart interface with ISO date-range selection, local/SQL history-source parity, bounded point counts and min/max-preserving downsampling. Mobile clients now receive actual timestamps, the selected source, returned-point count and last available record, so old local graph data is not presented as current SQL history and empty periods are reported clearly.

July 27 2026
------------
(Martin Pihrt) - CHMI v1.0.2<br/>
Corrected the animated radar location readout so every displayed frame shows the exact RGB value of the location pixel even when it is below the rain threshold. Added a color sample, per-frame rain/no-rain result and the surrounding detection-area statistics. The city-wide “no rain in any city” message is now produced only when “Where it is raining” analysis is enabled. Moved CHMI page styling from the template to a dedicated CSS file and added radar-pixel regression tests.

(Martin Pihrt) - Wind Speed Monitor v1.1.0<br/>
Split the plug-in into a live overview and a dedicated settings page. The overview now refreshes current speed, maximum, status and a one-minute rising/steady/falling trend through JSON without reloading, while retaining the selectable history graph. Fixed decimal calibration and threshold fields so both decimal points and commas are accepted. Reworked PCF8583 measurement to validate event-counter mode and BCD digits, read registers 0x01–0x03 directly, and divide pulses by the actual monotonic measurement duration instead of an assumed ten seconds, preventing shared-I2C wait time from producing false speed spikes. Added an enabled-by-default configurable plausibility ceiling, consecutive confirmation for station/e-mail safety actions, rejected-reading isolation, bounded rotating I2C diagnostic logging with display/download/delete controls, expanded health details, external responsive CSS, updated help/README, and automated calculation and validation tests.

July 26 2026
------------
(Martin Pihrt) - Weather-based Water Level v1.1.0<br/>
Added a calculation-method selector with the backward-compatible multi-day weather balance, configurable Zimmerman calculation and full FAO-56 ETo mode using OSPy's weather-provider or fallback ETo. Added method-specific settings and calculation details, safe neutral/stale-result handling, method-aware diagnostics, responsive external CSS, formulas and operating guidance in the plug-in help and README, and automated formula regression tests. Corrected the original method's relative-humidity handling by converting OSPy's normalized 0–1 value to percent before applying the humidity factor.

July 24 2026
-----------
(Martin Pihrt) - Astro Sunrise and Sunset v1.0.1<br/>
Removed the duplicate manual location, region, time-zone and coordinate fields. A selected Astral city still has priority; when no city is selected, the plug-in now uses the weather location managed by OSPy and the host system time zone. Missing OSPy weather/location settings are shown with a direct settings link and as a health warning.

(Martin Pihrt) - Water Consumption Counter v1.2.4 and E-mail Notifications SSL v1.1.4<br/>
Removed the redundant plug-in version rendered inside both settings pages. OSPy already displays the authoritative version from `plugin.json` in its common plug-in information bar.

(Martin Pihrt) - CHMI v1.0.1<br/>
Removed the redundant location/map row from the CHMI settings page. CHMI now exclusively uses the validated location managed by OSPy weather settings; disabling weather also disables local radar evaluation even if old coordinates remain stored. When weather or its location is unavailable, the plug-in shows a direct link to the OSPy weather settings and reports the missing prerequisite through health diagnostics.

(Martin Pihrt) - Water Consumption Counter v1.2.3, E-mail Notifications SSL v1.1.3, Air Temperature and Humidity Monitor v1.0.3, MQTT v1.0.1 and LCD Display v1.0.1<br/>
Moved virtual master-counter persistence and optional e-mail delivery out of OSPy's synchronous output callback into the plug-in worker, preserving the original output-event timestamp while preventing SMTP or settings storage from delaying the scheduler. Water Consumption Counter now refreshes its settings overview every two seconds without a page reload and checkpoints each running master total every ten seconds, limiting data loss if a final master-OFF event is interrupted. E-mail Notifications SSL now checks whether every optional data-provider plug-in is actually running before reading it; disabled tank, temperature, current-loop, water-counter or Shelly providers are skipped without aborting the remaining e-mail. Air Temperature and Humidity Monitor now quietly skips optional SQL logging while Database Connector is stopped instead of repeatedly reporting a plug-in proxy exception. MQTT no longer leaves module-import signal receivers behind, and both MQTT and LCD Display disconnect their receivers during plug-in shutdown so restarting either plug-in cannot create stale or duplicate callbacks.

July 22 2026
-----------
(Martin Pihrt) - E-mail Notifications SSL v1.1.2 and Water Consumption Counter v1.2.1<br/>
Added exactly one empty line between independent HTML e-mail sections. Completed-run e-mails now briefly wait for the master OFF counter update, and the virtual water-meter report uses the station-duration estimate as a display-only fallback when that update is not yet available, preventing a misleading zero master-run consumption.

(Martin Pihrt) - E-mail Notifications SSL v1.1.1<br/>
Removed inconsistent blank space between generated e-mail sections. Section headings now use one controlled line break, sensor blocks no longer append an extra empty line, the local OSPy address is emitted without a margin-bearing paragraph, and the final MIME body no longer wraps generated block content in an invalid outer paragraph.

(Martin Pihrt) - Water Consumption Counter v1.2.0 and E-mail Notifications SSL v1.1.0<br/>
Changed Home timeline values to show increasing virtual consumption without repeating the configured flow, with automatic cubic-meter formatting from 1000 liters. Added a read-only completed-run report and extended the SSL e-mail plug-in's existing water-counter option to include master consumption during the station run, total master consumption and completed station consumption. Missing or unavailable counter data never blocks the remaining e-mail. Moved the SSL switch styling from the template to a versioned static CSS file and exposed its plug-in version on the settings page.

(Martin Pihrt) - Water Consumption Counter v1.1.1<br/>
Added the standard blue rounded border around the plug-in interface.

(Martin Pihrt) - Declared permission approval documentation<br/>
Documented the OSPy 3.0.294 administrator-approval rules for permissions declared in `plugin.json`, including backward-compatible approval of already installed plug-ins, renewed approval only when an update adds permissions and automatic-update blocking until review. No plug-in code, manifest or version was changed.

(Martin Pihrt) - Water Consumption Counter v1.1.0<br/>
Reworked the settings page into a responsive overview with separate master totals, current-run values, configured flow, active station summaries, e-mail settings and collapsible activity history. Added live `showOnTimeline` publishing: each active master displays the total estimated consumption since the last reset, while every running station assigned to a master displays only its estimated consumption for the current run and the applicable flow rate. Moved all plug-in styling into a versioned static stylesheet and retained the existing settings, counters, reset and e-mail behavior. The manifest requires OSPy 3.0.296, which contains station-ID based live timeline refresh, so older stable installations are prompted to update OSPy before installing this plug-in revision.

July 21 2026
-----------
(Martin Pihrt) - Automated plug-in tests<br/>
Expanded required GitHub Actions compatibility testing to Python 3.11 and the latest stable Python 3.14. Every plug-in revision is now tested in four combinations covering both Python versions and both OSPy `master` and OSPy `beta`; all combinations must pass before promotion to the stable channel.

July 20 2026
-----------
(Martin Pihrt) - System Update v1.2.4<br/>
Added verified stable releases based on annotated semantic Git tags (`vX.Y.Z`) reachable from `origin/master`. The status page now shows the exact running and target commits, stable tag, date and tag release notes. Added a dedicated rollback to the latest verified stable release and hardened manual commit rollback with settings persistence, a verified safety backup, external watchdog protection, immediate recovery on failure and a single restart. Stable rollback revalidates repository tags server-side and checks out `master`; lightweight, malformed and non-master tags are ignored. Manual rollback now uses full commit identifiers while displaying a compact hash. Moved all System Update page styling from its HTML template into plug-in static CSS and added regression coverage for tag validation, presentation and rollback ordering.

July 19 2026
-----------
(Martin Pihrt) - System Update v1.2.3<br/>
Fixed a false `rollback_failed` result on legacy SysV installations. Their generated systemd restart job can spend 30 seconds stopping OSPy, exactly matching the former watchdog subprocess timeout; systemd still completed the restart after the client timed out, but the successful repository rollback was reported as failed. The watchdog now submits a non-blocking systemd restart job, or starts the SysV restart command as a detached process when systemd is unavailable, after recording the successful rollback.

(Martin Pihrt) - System Update v1.2.2<br/>
Fixed automatic rollback on OSPy installations managed by the legacy SysV init script. That script can terminate every `/usr/bin/python3` process during restart, including the Python watchdog helper. The watchdog now runs below a non-Python shell supervisor that relaunches a helper killed by the legacy cleanup while recovery remains pending. A token-bound readiness marker must also be received before any Git-tracked OSPy files are changed; a transient service that exits or never loads its recovery state causes the update to stop. Added regression coverage for readiness, supervisor relaunch and safe PID-only SysV shutdown.

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
