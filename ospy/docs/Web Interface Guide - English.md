OSPy Web Interface Guide in English
====

    OSPy installation
    Logging in
    Home page
        Normal - Water Level
        Active - Rain Delay
        Schedule - Manual
        Enabled - Disabled
        Stop All Stations
        Water balance Graph
        Suppressed by Rain Delay
        Rain sensed
        CPU Temp
        CPU Usage
        Software version
        External IP
        Working
        Diagnostics
    Feedback
    Programs page
        Add a New Program
        Program groups
        Add group
        Rename group
        Enable or Disable a group
        Copy group
        Delete group
        Run Now
        Edit
        Copy
        Move to group
        Delete All
        Enable or Disable a Program
        Conflict warnings
        Schedule type
            Selected days (Simple)
                Start time
                Duration
                Repeat
                Repetitions
                Pause
            Selected days (Advanced)
                Schedule
            Repeating (Simple)
                Water interval
                Starting in
                Start time
                Duration
                Repeat
                Repetitions
                Pause
            Repeating (Advanced)
                Water interval
                Starting in
                Schedule
            Weekly (Advanced)
                Monday-Sunday
            Custom
                Water interval
                Starting in
                Day 1 - Day 7
            Weekly (Weather based)
                Irrigation min
                Irrigation max
                Run max
                Pause ratio
                Preferred Execution Moments
                    Day
                    Start time
                    Priority
                    Add - Delete
        No adjustments
        Cut-off
        Activate Master
    Run Once page
        Run Now
        Reset Time
    Plugins page
        Manage
        Install New Plugin
            Custom plug-in (ZIP)
            Github (https://github.com/martinpihrt/OSPy-plugins/archive/master.zip)
        Disable All
        Enable All
        Enable check updates
        Load changes
        Changes
        Automatic updates
    Log page
        Events log
        Download log as
        Clear Log
        Clear Log Email
    Options page
        System Section
            Show Tooltips
            Set System name
            Select System theme
            Clock format
            HTTP IP addr
                About the port number
            HTTP/S port
            Show plugins on home
            Show sensors on home
            Select Language
            Show pictures at stations
        Weather Section
            Use Weather
            Weather provider
            Stormglass API key
            Location
        Users Section
            Disable security
            Admin login name
            Current password
            New password
            Confirm password
            Aditional users
        Security Section
            Form protection
            Use HTTPS access
            Domain name
            Use Own HTTPS access
            API CORS allowed origin
            Enable API JSONP
            Remembered browser logins
        Sensors Section
            Password for uploading
        Station Handling Section
            Maximum usage
                About Sequential and Concurrent modes
            Number of outputs
            Pause between stations
            Minimum runtime
        Configure Master Section
            Master station
            Master two station
            Activate relay
            Master start offset
            Master stop offset
            Master two start offset
            Master two stop offset
        Rain Sensor Section
            Use rain sensor
            Normally open
            Set rain delay
            Rain delay time
        Logging Section
            Enable run log
            Max run entries
            Enable email log
            Max email entries
            Enable events log
            Max events entries
            Enable debug log
        System Restart Section
            Restart
            Reboot
            Shutdown
            Default
        System Backup Section
            Download
            Upload
        SSL Certificate
            Upload
            Generate
    Stations page
        Station
        Name
        Usage
        Precipitation
        Capacity
        ETo factor
        Balance adjustment
        Connected
        Ignore Rain
        Activate Master?
            None
            Activate Master
            Activate Master Two
            Activate Master 1/2 by program
        Notes
        Image
    Sensors page
        Add a New Sensor
            Sensor Parameters
        Delete All sensors
    Help page
        OSPy
            Readme
            Changelog
            Programs
            Web Interface Guide - Czech
            Web Interface Guide - English
            Web Interface Guide - German
            Web Interface Guide - Polish
            Web Interface Guide - Russian
            Web Interface Guide - Serbian
            Web Interface Guide - Slovak
        API
            Readme
            Details
        Plug-ins
            Readme
            Usage Statistics
            LCD Display
            Pressure Monitor
            Voice Notification
            Pulse Output Test
            Button Control
            CLI Control
            System Watchdog
            Voltage and Temperature Monitor
            Remote Notifications
            System Information
            MQTT
            Air Temperature and Humidity Monitor
            Wind Speed Monitor
            Weather-based Rain Delay
            Relay Test
            UPS Monitor
            Water Consumption Counter
            SMS Modem
            Signaling Examples
            Email Notifications
            Remote FTP Control
            System Update
            Water Meter
            Webcam Monitor
            Weather-based Water Level Netatmo
            Direct 16 Relay Outputs
            MQTT Zone Broadcaster
            System Debug Information
            Weather-based Water Level
            Real Time and NTP time
            Water Tank
            Humidity Monitor
            Monthly Water Level
            Pressurizer
            Ping monitor
            Temperature Switch
            Pool Heating
            E-mail Notifications SSL
            Sunrise and Sunset
            Photovoltaic Boiler
            IP CAM
            Modbus stations
            CHMI
            Proto
            Label Maker
            IP Scanner
            Database Connector
            OSPy Backup
            MQTT Home Assistant
            Shelly Cloud Integration
            Current loop tanks monitor

----

# OSPy installation
The recommended clean installation uses Raspberry Pi OS or Debian 12 and Python 3.11 or newer. The installer always downloads the stable OSPy `master` branch. On first start, the login page displays a generated administrator password; change it immediately in Options after signing in.

## USING THE INSTALLATION SCRIPT
Login to the Pi using SSH. Type or copy and paste the following command:
Remember: Raspberry Pi commands are case sensitive.

```bash
wget https://raw.githubusercontent.com/martinpihrt/OSPy/master/ospy_setup.sh
sudo bash ospy_setup.sh
```

The menu separates core requirements from optional MQTT and multimedia packages. Choose `/opt` or the invoking user's home directory. The installer never deletes, resets or automatically updates an existing Git checkout. It builds the service from the versioned systemd template, starts it and verifies its state; recent service output is shown when startup fails. A reboot is recommended only for I2C or group changes. Open a successful installation on port 8080. The **Clean installation** Help document contains the detailed safe procedure, manual update and local account recovery instructions.

----

# Logging out
After clicking the "Logging out" button, the user logs out of the system.

----

# Two-factor security (2FA)
Two-factor authentication protects the main administrator account with a second verification step after the password. Open **Options → Two-factor security → Configure** and choose exactly one method: **Authenticator application (TOTP)**, **Code sent by e-mail**, or **Disabled**. The two methods cannot be active at the same time.

For TOTP, run `python setup.py install` once if QR support is reported missing. Scan the displayed QR code with Google Authenticator, Microsoft Authenticator, 2FAS, Aegis, or another TOTP application, then enter its current six-digit code. OSPy activates the secret only after this confirmation. Correct system time is required for TOTP.

E-mail verification is available only while **E-mail Notifications SSL** is installed, running, and has its SMTP server, account, password, and recipient configured. When enabling it, OSPy sends a confirmation code immediately. Login codes expire after five minutes and are never placed in the plug-in's retry queue.

After enabling either method, save the displayed one-time backup codes in a safe place. Each code can replace the normal second factor once and is then deleted. They are not shown again. Changing or disabling 2FA revokes all remembered browser logins. A remembered browser is trusted only after a complete password and second-factor login. If the phone is lost or e-mail is unavailable, use a backup code; without a backup code, restore a configuration backup or reset the 2FA settings locally on the OSPy device.
    Logging out

----

# Logging in
The login page presents a text field for entering a name and password. The default name is **admin**. During the first installation, a random password will be generated (this password must then be changed to a different password in the settings! On the page - tab "Options page" it is recommended to change the password (or even the name) to your own new password.
Enter name, password and click the **LOG IN** button.


----

# Home page
The home page is the main control center of the web interface. This includes:

* Clock showing current time On all pages.
* Navigation bar at the top for moving between pages. The interface is also found on other pages besides the login page.
* A set of buttons for making global changes to system behavior.
* A timeline that provides information about completed and scheduled irrigation events.
* A graph that provides information about irrigation events.
* The footer that is present on all pages (if the user is logged in). The footer contains: CPU Temp, CPU Usage, Software version, External IP, Working.
* Some extensions can inject homepage and add other elements. For example, the astral extension adds graphical representations of sunrise and sunset to the timeline. Extension tank monitor graphic column with volume and amount of water.


## Normal - Water Level
A button that allows you to set the "water level" as a percentage of the total run time for all irrigation programs (for programs, increase or decrease their set time).

## Active - Rain Delay
Rain delay. A button that allows watering to be paused for a specified period of time for all stations except those that have been set to ignore rain on the Stations page.

## Schedule - Manual
Schedule - Manual. A button that switches the system between schedule (automatic mode) and manual mode, which allows direct control of stations.

## Enabled - Disabled
Button for enabling or disabling the running of the OSPy program (when disabled, the scheduler will not run).

## Stop All Stations
The "Stop All Stations" button is used to immediately cancel a running irrigation program or an active station.

## Water balance Graph
If at least one program is configured in the scheduler, a graph showing the amount of water supplied for each station/program is drawn at the bottom of the screen.

## Suppressed by Rain Delay
If the rain delay is enabled, "Suppressed by Rain Delay" will be displayed and all stations (except those set to ignore rain on the Stations page) will be blocked for a period of time.

## Rain sensed
If the rain sensor is activated, "Rain sensed" will be displayed and all stations (except those set to ignore rain on the Stations page) will be blocked.

## CPU Temp
Raspberry pi processor temperature. The displayed temperature can be switched between C and F.

## CPU Usage
Raspberry Pi CPU usage. Usage is shown in %.

## Software version
Link to the project software repository and the revision number of the installed software.
Stable builds checked out from `master` use the numeric version, for example `3.0.238`. Test builds checked out from `beta` show the same revision with the `-beta` suffix, for example `3.0.238-beta`. Promoting that commit to `master` removes the suffix without changing the revision number.

### Safe update and automatic rollback

Before every update, the System Update plug-in first saves the settings and creates a verified safety backup. It then starts an external watchdog before changing any Git-tracked files. On systemd installations, the watchdog runs in a separate transient service and remains active while OSPy restarts. A detached helper process is used without systemd.

The new OSPy process confirms a successful update only after the scheduler records a fresh heartbeat and the web interface starts accepting connections. If a healthy start is not confirmed within 120 seconds, the watchdog automatically restores the previous commit and original branch and restarts OSPy. If the watchdog cannot be started, the update stops before tracked files are changed. The watchdog result is also available in Diagnostics as part of the System Update plug-in health information.

System Update displays the full commit of the running revision and the exact target commit from the selected channel. It recognizes a verified stable release only as an annotated Git tag named `vX.Y.Z` whose commit is reachable from `origin/master`. The annotated tag message is used as the short release notes. Lightweight tags, other names and tags outside `master` are not offered.

Rolling back to the last verified stable release or manually to an older commit first saves the settings, creates a verified safety backup and starts the same external watchdog as a normal update. A stable rollback switches the working branch to `master`. The project maintainer creates release tags manually only after successful tests; the plug-in never creates tags itself.

## External IP
External IP address for the OSPy system (address of your connection provider - router). Tested via pihrt.com.

## Working
The time the Raspberry pi system has been running since it was powered on (or restarted).

## Diagnostics
The **Database** row also shows the active settings storage and SQLite readiness. This transition release continues to read and write the existing shelve/DBM files. The readiness check uses only a temporary in-memory database and by itself creates no file or data migration. If Python SQLite support is unavailable, OSPy continues using shelve/DBM and reports the reason as passive information rather than a system failure.

After each successful settings save, OSPy creates a verified `options.sqlite3` shadow copy next to the active shelve/DBM files. It is written through a temporary file and atomically replaced only after schema, key, value and integrity checks succeed. OSPy never loads settings from the shadow during startup. A synchronization failure leaves the authoritative shelve save intact and appears as a warning in the **Database** row; a missing shadow waits for the next settings save.

At startup OSPy compares the authoritative shelve values with SHA-256 hashes stored in shadow schema 2. It does not unpickle shadow values during this automatic comparison and never uses them to recover or start OSPy. A matching shadow is marked verified; missing, changed or unexpected keys and checksum or database damage are reported as warnings while shelve remains in use. A schema 1 shadow from the preceding transition phase is not read and is replaced safely on the next settings save.

At startup and after every successful shadow replacement, OSPy performs a dry-run decode only after every key and checksum matches a single read-only snapshot, then applies the normal settings validation to the reconstructed SQLite values. The reconstructed dictionary is discarded and never assigned to the running configuration. Diagnostics reports whether this SQLite read test passed; failure remains a warning and OSPy continues exclusively with the already active shelve settings.

Shadow schema 3 also contains a manifest with the total record count and a checksum over the complete sorted key/checksum list. This independently detects removed or added rows before decoding. OSPy performs and discards a full recovery dry run for both the current SQLite shadow and the previous shadow in the backup directory. Diagnostics reports both results. A failed or unavailable recovery candidate never changes startup selection; shelve/DBM remains authoritative.

At startup OSPy uses the first independently verified SQLite candidate only for a restore rehearsal in an isolated temporary directory. It creates a temporary shelve/DBM database, reopens it, validates every setting, compares the serialized values and then removes the directory. Neither the active database nor the startup settings source is changed. If the current SQLite copy is damaged, the rehearsal may use the verified backup while running settings still load from authoritative shelve. The **Database** row in Diagnostics reports the result, source and setting count.

OSPy also only simulates the emergency decision that would be made if every shelve/DBM database were invalid. The independently verified current SQLite copy has priority; the verified backup would be selected only if the current copy failed. The selected dictionary is discarded and never assigned to running settings, so this state still does not activate SQLite recovery. Diagnostics reports readiness, the hypothetical source and the setting count.

The experimental **Allow emergency SQLite settings recovery** option in **Settings storage** is disabled by default. When enabled, OSPy creates a non-secret atomic activation marker only after independently verifying a schema-3 SQLite copy; the verified copy itself must also contain the enabled option, so neither the marker nor the database authorizes recovery alone. Recovery is attempted only when the current, temporary and backup shelve/DBM databases are all invalid. OSPy prefers current SQLite, falls back to the verified backup, rebuilds and revalidates a shelve database in the temporary directory, and only then loads it. This step does not overwrite the existing current or backup directories, and normal persistence remains shelve/DBM. Disabling removes the marker before writing settings. Diagnostics and the startup recovery message identify actual use or failure; review the system and create a backup after recovery.

The experimental **Prefer verified SQLite settings reads** option in **Settings storage** is also disabled by default. When enabled, OSPy always loads and validates shelve/DBM first, compares the complete SQLite key and checksum set with that exact authoritative snapshot, and independently decodes and validates every value. Only a complete match assigns the equivalent SQLite dictionary to the running settings. A missing copy, difference, corruption or decode failure keeps the already loaded shelve values without interruption. Writes, directory rotation and backups continue to use shelve/DBM exclusively; SQLite remains a verified shadow. Diagnostics reports whether the path was used, disabled or fell back to shelve.

The experimental **Require verified SQLite for settings commits** option in **Settings storage** is disabled by default. When enabled, a new settings directory may replace active data only after both its temporary shelve/DBM database and SQLite copy are written and independently verified. If SQLite is unavailable or writing or verification fails, OSPy removes the complete uncommitted temporary directory, preserves the previous active settings and last-save timestamp, and reports a settings-write problem. Disabling restores compatible shelve-first behavior. A successful strict commit can be read through the verified SQLite path, but shelve/DBM remains the persistence and backup format. Diagnostics reports the active commit policy.

Diagnostics keeps non-authoritative **SQLite migration evidence**: consecutive successful starts using verified reads and consecutive strict dual-writes. A failure resets only the relevant streak and records its time and reason. The separately and atomically written status file contains no settings and is never used for startup, recovery or storage selection.

During early startup, the interface language is still loaded first from a valid shelve/DBM database. When verified SQLite reads are enabled, the bootstrap compares every key and checksum with that exact shelve snapshot and reads only the `lang` value from SQLite after a complete match. A missing, older, different or damaged SQLite copy always falls back safely to the shelve language. Checking a missing database does not create an empty file.

The **Settings storage mode** selector groups the safe transition controls. **Compatible** keeps shelve/DBM authoritative with SQLite as an optional shadow. **Verification** enables emergency recovery, verified reads and strict dual-write; it still does not make SQLite the primary database. The individual switches remain available for advanced control, and a mixed combination is automatically labelled **Custom advanced settings**. Existing installations derive the mode from their saved switches without changing their values.

The **Diagnostics** button in the footer opens an administrator page for checking how OSPy and its plug-ins are using the system.

When Diagnostics reports an error, it opens a red window with the problem, available details, a possible solution and a link to the related page. Administrators can also show the same window on the Home page by enabling **Options > Diagnostics > Show diagnostic errors on the home page**. This error window has priority over the update notification. Disabling the option affects only the Home page; errors remain visible in Diagnostics.

The page uses collapsible **System status**, **Performance and processes**, and **Security check** sections. Select a dark section bar to expand or collapse it. **System status** gives each operational area an OK, warning, error or not-configured state. It monitors the scheduler heartbeat, the last successful schedule calculation and next run, output command writes, sensor communication, settings database accessibility, free disk space, enabled plug-in failures, e-mail readiness, weather, internet connectivity and the newest available backup. A successful output write confirms that OSPy sent the requested state to the output driver; it does not claim that a physical relay switched unless hardware feedback is available.

**Security check** passively assesses HTTPS, anonymous access, two-factor authentication, sensor API authentication, API CSRF protection, CORS, the sensor password and recommended HTTP response headers. It never displays the sensor password and does not change any setting. The **Home network** profile treats selected compatibility compromises as warnings, while **Internet access** requires encrypted, authenticated and restricted access. Every finding explains the current state, a recommendation and a link to the related settings. A reverse proxy may add HTTP security headers after the response leaves OSPy; Diagnostics reports only what OSPy itself can guarantee.

Caught core operational failures appear in **System status** as separate active problems. Each entry identifies the affected component, occurrence count, latest occurrence, technical cause and a recommended recovery action. A successful retry automatically clears the active problem, while the full traceback remains in the event log. Expected compatibility fallbacks are not reported as failures.

The collapsible **Incident history** section retains up to 200 recent problems across OSPy restarts. It can filter all, active, resolved and restart-interrupted incidents. Repetition of the same active problem increments its count instead of creating duplicates; the table shows when it opened, last occurred and resolved. History is atomically stored in a validated size-limited JSON file and does not duplicate full tracebacks.

The system summary shows current CPU usage, CPU temperature, system uptime, load average, OSPy process CPU usage, OSPy memory usage, thread count, platform information and the last refresh time.

The plug-in table shows every available plug-in, whether it is running and enabled, its own operational health, current CPU load, total CPU time, thread count, start time, restart count and available actions. A plug-in can optionally provide a `health()` function returning, for example, `{'status': 'ok', 'summary': '...', 'details': '...'}`; accepted states are `ok`, `warning`, `error` and `unknown`. Older plug-ins without this function remain fully compatible and show “not reported”. A failed or timed-out health check does not stop the plug-in or the Diagnostics page. Data refreshes automatically, so the page can be left open while watching system load.

By default, plug-ins are sorted by current CPU load from highest to lowest. Use **Sort plugins** to switch sorting to plug-in name or total CPU time when you want a stable list or want to find long-running CPU consumers.

The **Open** action opens the plug-in page. **Restart plugin** restarts only the selected running plug-in; it does not restart all of OSPy.

If a refresh warning is shown, the last automatic read from the diagnostics API failed or returned a controlled error. Existing data can remain visible until the next successful refresh, and the warning is cleared automatically after a successful refresh.

----

# Feedback
The **Feedback** button in the header, to the left of the system name, opens a page for reporting bugs, suggesting improvements and asking questions. The page is available to signed-in administrators and users; the button is hidden on the login page.

Choose **Bug report**, **Feature request** or **Question**, then enter a short title and a detailed description. **Continue to GitHub** opens a prefilled new GitHub Issue. The user signs in to GitHub, reviews the content and submits it there. OSPy does not store a GitHub access token and does not create an Issue before this confirmation.

The option to include system information is enabled by default and shows an exact preview before submission: the OSPy version and date, architecture, distribution and operating-system version, and Python version. The OSPy system name, operator name, IP addresses and unique usage-statistics identifier are excluded. Clear the option to send only the user's text.

**View existing reports** opens the project's GitHub Issues. **GitHub Discussions** opens the project discussions directly and is suitable for general questions and shared ideas. Screenshots and other files can be attached after GitHub opens.

The form uses the existing OSPy login and CSRF protection. When leaving for GitHub, the address of the open OSPy page is not sent as the HTTP referrer.

----

# Programs page
## Add a New Program
With the button "Add a New Program" we create a new scheduler program.

## Program groups
Programs can be organized into drop-down groups. Groups are suitable, for example, for separating summer and winter programs, or for a clear division by part of the garden.

## Add group
The "Add group" button creates a new program group.

## Rename group
The rename group action changes only the group name. Programs assigned to the group will be retained.

## Enable or Disable a group
A group ON/OFF action enables or disables all programs in that group at once. It is suitable, for example, for seasonal switching of several programs.

## Copy group
The copy action creates a new group and copies all programs from the original group into it. The copied programs are made disabled so they don't run until we check them.

## Delete group
Group deletion requires confirmation. Programs from the deleted group are moved to the default group.

## Postpone group
The "Postpone group" button next to "Add a New Program" moves the nearest scheduled run of the whole group once. Select a new date and start time for the first program; a preview of the original and new time range is shown before confirmation. The new start must be later than the original start, must be in the future, and can be set no more than 30 days ahead.

OSPy finds the nearest future run of every enabled program in the group and shifts all these runs by the same time difference. Program order, durations, and relative gaps are preserved. For example, a group scheduled today from 18:00 to 22:00 can be postponed until tomorrow at 07:00; the shifted run will then finish at approximately 11:00.

Postponement does not change the normal program definitions or their later scheduled days. Only the nearest original run is skipped once and its replacement runs at the new time. Postponed programs still respect the scheduler state, rain blocks, the rain sensor, output usage limits, and station delays. The postponement is saved in the settings and survives an OSPy service restart. Only one active postponement is allowed per group.

An active postponement is displayed beside the group as the original time, an arrow, and the new time. Use "Cancel postponement" to remove it. If the original time has not arrived, the normal original run is restored. If the original time has already arrived, it is not started again for safety; only the replacement run is cancelled. A group with an active postponement cannot be deleted; cancel the postponement first. Creating and cancelling a postponement is available only to an administrator and is protected by login and CSRF verification.

## Run Now
With the button "Run Now" we start the program immediately regardless of the time and date of the scheduler.

## Edit
The "Edit" button is used to modify the parameters of an already created program.

## Copy
The "Copy" button creates a copy of the selected program. Copy is disabled by default, so we can safely modify it before using it in the scheduler.

## Move to group
A program can be assigned to a group on the program edit page. This only changes its location on the Programs page.

## Delete All
The "Delete All" button removes all existing programs after confirmation.

## Enable or Disable a Program
The "ON/OFF" switch allows the created program to be enabled or disabled in the scheduler.

## Conflict warnings
When saving a program, OSPy checks the allowed programs and looks for overlaps of the scheduled run on the same station/output. If another program is scheduled at the same time, the Programs page will display a notification with the overlap time. This is just a warning, the program will not be automatically blocked or modified.

## Schedule type
Scheduler type allows to choose the suitable program type according to our requirement (selected days, repeat, weekly, custom and programs based on weather forecast).

### Selected days (Simple)

#### Start time

#### Duration

#### Repeat

#### Repetitions

#### Pause

### Selected days (Advanced)

#### Schedule

### Repeating (Simple)

#### Water interval

#### Starting in

#### Start time

#### Duration

#### Repeat

#### Repetitions

#### Pause

### Repeating (Advanced)

#### Water interval

#### Starting in

#### Schedule

### Weekly (Advanced)

#### Monday-Sunday

### Custom

#### Water interval

#### Starting in

#### Day 1 - Day 7

### Weekly (Weather based)

#### Irrigation min

#### Irrigation max

#### Run max

#### Pause ratio

#### Preferred Execution Moments

#### Day

#### Start time

#### Priority

#### Add - Delete

## No adjustments
No modifications will be applied to this program (for example shortening or extending the time)

## Cut-off
If the adjusted running time of the program would be shorter than this set time, the program will be skipped (for example, the adjusted running time from the weather forecast extension, or the monthly adjustment of the amount of water and other extensions). The time is set in percentages.

## Activate Master
All stations that have the "Activate Master 1/2 by Program" option set will activate Master Station 1/2 according to this assignment in the program. Notification! for stations that have the option "Activate main 1/2 by program" set, the control option "run once" and "manual_on" cannot be used. Only the station will start, not the main station (1 or 2)! This setting is only available if you are using both master stations!

----

# Run Once page

The "Run Once page" page presents a list of allowed stations with a minute and second field for each. This site can be used to test and provide additional irrigation on a one-time basis.

## Run Now
The button activates all selected preset stations.

## Reset Time
The button will delete all preset times for all stations.

----

# Plugins page

On the page "Plugins page" we can configure or control all extensions in the OSPy system.

## Manage

Clicking the "Manage" button will open the extension manager window in OSPy. All available extensions can be turned on, off, installed from repository, etc...

A plug-in uses a `plugin.json` file containing its name, version, description, author, homepage and license. The manager displays this metadata when available. Backward compatibility is retained for older plug-ins already installed without a manifest, and OSPy reads their name from `__init__.py`; the rules for new installations are described below.

The manifest may declare dependencies on other plug-ins by directory name in the `dependencies` list. A required dependency must be installed and enabled. An optional dependency does not block the consumer, but when both plug-ins are enabled OSPy starts the provider first. Shutdown uses the reverse order, and dependency cycles are not started. A bulk installation may provide a required dependency in the same ZIP; installing only the consumer requires its provider to be installed already.

Before activation OSPy checks declared OSPy and Python versions, required Python modules, supported platforms, GPIO/I²C availability and conflicts with enabled plug-ins, GPIO pins or I²C addresses. A blocking problem prevents activation and Enable All skips the affected plug-in. Plug-in management and Diagnostics show details and declared network, file, I²C, GPIO, e-mail, subprocess or system permissions. Permissions inform the administrator; they are not an isolated operating-system sandbox.

New plug-ins can use the shared thread lifecycle and OSPy stop signal. When disabling a plug-in, OSPy first sends the stop signal, calls its existing `stop()` function and waits up to five seconds for registered threads. Threads that remain alive are reported as an error in Diagnostics and prevent a second copy of the plug-in from starting. Existing plug-ins without this interface remain compatible.

Before import and startup, an automatic static test runs without executing plug-in code or accessing hardware. It checks the directory, `__init__.py`, Python source syntax and size, the optional manifest and, for manifest-based plug-ins, declared `start()` and `stop()` functions; legacy plug-ins without a manifest retain their existing compatibility. Symbolic links are not followed. An error prevents activation and details are available in Plug-in management and Diagnostics. Compatibility, manifest and test information use high-contrast status panels in Plug-in management so they remain readable for both enabled and disabled plug-ins.

## Install New Plugin

Clicking the "Install New Plugin" button opens a window with a remote repository where we can select the available extensions to install on the OSPy system and read general information about the extensions.

Before copying any files, OSPy safely reads `plugin.json` directly from the downloaded ZIP archive and displays the compatibility state and specific reasons for any problem for each plug-in. An incompatible plug-in cannot be installed or updated manually. A plug-in with warnings remains installable after the warnings are shown. Bulk installation installs compatible plug-ins and skips incompatible ones while reporting the reasons. The same validation applies to custom ZIP files, individual and bulk operations, and updates. A missing, invalid, or oversized `plugin.json` is an installation error for a new installation; already installed legacy plug-ins without a manifest can continue to run in backward-compatibility mode.

### Custom plug-in (ZIP)
OSPy validates the complete ZIP before writing any plug-in file. The archive must contain at least one plug-in directory with `__init__.py` and a valid UTF-8 `plugin.json` whose `id` matches the directory name. A plug-in may also contain Python modules, `README.md`, `templates`, `static`, `script`, `docs`, `i18n` and `data`. A repository archive may place plug-ins below `plugins/`; a custom archive may contain a plug-in directly at its top level.

Absolute or parent-directory paths, non-portable names, duplicate paths or plug-in identifiers, symbolic links, special or encrypted entries and damaged archives are rejected. Limits are 64 MiB downloaded ZIP data, 4,096 archive entries, 256 plug-ins, 32 MiB per expanded file, 128 MiB total expanded data and a maximum compression ratio of 200:1. Installation is atomic for each plug-in: files are prepared first, existing `data` is preserved, and a failed replacement or start restores the previous version.

The extension manager allows you to install your own extension in the OSPy system, which is not published in the remote repository (for example, your personal extension). Using the "browse" button, we select the desired file on our computer to install into the OSPy system. The extension file (zip) must contain the complete structure of the extension (init, templates, i18n, readme, etc.).

The plug-in manager uses the stable `master` channel by default. An administrator can switch to the test `beta` channel; the selected channel is visible in management and installation and is used for the list, manual installations, bulk operations and automatic updates. Test versions may contain errors. Switching channels discards the downloaded cache for the previous branch, and the next check loads data from the new branch. Opening an installed plug-in page displays its name and the version read from `plugin.json` above the plug-in content.

### Github (https://github.com/martinpihrt/OSPy-plugins/archive/master.zip)
There is a repository of available extensions for the OSPy system at the above location.

Installing or updating an extension runs code from the selected source. OSPy will display the repository URL and ask for confirmation before installing or updating. The Fetch Changes action while contacting the remote repository displays a message about the check in progress.

## Disable All
The button disables all installed extensions.

## Enable All
The button will enable all installed extensions.

## Enable check updates
When the button is active, the availability of a new version of the extension is automatically checked in the remote repository after an hour. When a new version is available, an "update" message will appear next to the extension.

## Load changes
The button retrieves the latest list of available changes from the remote extension repository.

## Changes
The button opens an overview of available extension changes and update information.

## Automatic updates
When the button is active, this extension will automatically be updated when a new compatible version is available. An incompatible new version is not installed automatically, and the manager displays the reason. Warning: OSPy is constantly evolving and if there is a major change in OSPy and the user does not update OSPy, the extension may not work after the update. Always update OSPy first and then all extensions!

----

# Log page
Using the page "Log page" we can view all the logs recorded in the OSPy system. The number of records is set on the "Options page" page.

## Events log
The Events log is an operational and audit history separate from both the station-run log and the technical debug log. It records irrigation interventions and blocked runs, configuration changes, users and security events, system and plug-in operations, and sensor events or conditions. Each record shows the date, time, severity, category, subject, and details. Severity is also distinguished by color: information is blue, success green, warning amber, error red, and critical dark red. Use the **Event category** selector to show all events or one category. The `events.csv` export contains Date, Time, Level, Category, Subject, and Status. The existing debug logging and its `events.log` file are not affected by these controls.

The same audit log records state-changing operations performed through the authenticated API, including station and program control, configuration changes, log clearing, and system actions. Failed API authentication and temporary brute-force blocking appear under **Users and security**. Routine API reads and each successful Basic authentication are not recorded, preventing high-frequency API traffic from filling the log.

## Download log as
The "Download record as Excel log.csv" link allows you to save the record of the irrigation run as a csv file (Excel program) to your computer.
* The structure of the table is: Date, Start Time, Zone, Duration, Program. Dates are separated by a comma.
* Example: 2019-08-12 05:00:00 Filtering 60:00 Filtering

Link "Download log as Excel log email.csv." allows you to save a record of sent emails to your computer as a csv file (Excel program).
* The structure of the table is: Date, Time, Subject, Body, Status. Dates are separated by a comma.
* Example: 2019-08-12 06:00:04 Sent COTTAGE SYSTEM Finished watering -> Program: Filtration, Station: Filtration, Start: 2019-08-12 05:00:00, Duration: 60:00, Water -> Amount of water in tank: Level: 170 cm (90 %), Ping: 95 cm, Volume: 1.28 m3, Temperature DS1-DS6 -> CELLAR: 21.1 ℃ PUMP: 33.5 ℃ BOILER: 26.6 ℃ INDOOR: 22.1 ℃ WELL: 12.2 ℃

## Clear Log
Pressing the "Clear Log" button will delete all records of the irrigation run. The action is non-refundable.

## Clear Log Email
After pressing the "Clear Log Email" button, all records of sent emails will be deleted from the system. The action is non-refundable.

----

# Options page
On the page "Options page" we can edit the settings of the entire OSPy system.
The page contains several collapsible sections. Click on the bar to open or close the desired section.

### Show Tooltips

* Click the "Show Help" button to show or hide information about each option.

### Set System name
System naming is useful when working with multiple OSPy systems.

* Enter a unique descriptive name for the system.
* Click the "Confirm Changes" button at the bottom of the page to save your changes.

The system name defaults to "OpenSprinkler Pi" and will be displayed in the header of each page for easy system identification.

### Select System theme
Specifies the appearance of the GUI. Several themes are available in the list (green mode, black and white mode...)

### Clock format
The 24-hour time option chooses between the international 24-hour format, sometimes referred to as military time, and the 12-hour-AM / PM format.

* Uncheck the box and select 12 hour AM/PM format.
* Click the "Confirm Changes" button at the bottom of the page to save your changes.

You will be redirected to the home page and the clock will be in the selected format.

### HTTP IP addr
IP address for the HTTP/S server. IPv4 or IPv6 address (will only appear after reboot.) Default is 0.0.0.0.

#### About the port number
The HTTP/S port number is part of the web address.
Port 80 is the default number for web pages and as such may not be included when a URL is entered into the browser's address bar. Many web servers use port 80 by default.
If you run another server on the same Raspberry Pi as OSPy and use the same port number, a conflict will occur and OSPy may not start.
You can avoid the conflict by changing the OSPy port number on the Options page to something else, such as 8080. If you change the port number that OSPy uses, you will need to include that number preceded by a colon in the URL for the OSPy web interface. For example:
[URL Raspberry pi]: 8080

### HTTP/S port
The HTTP/S port number is part of the web address. Port 80 is the default number for websites.

* Click in the text box next to the HTTP/S port option.
* Enter the port number you want to use, eg 8080.
* Click the "Confirm Changes" button at the bottom of the page.

You will return to the home page. The system reboots, but no reboot indication is visible in the web interface. Wait at least 60 seconds, then add the new port number to the Pi URL preceded by a colon (:) and try to connect to OSPy again.

### Show plugins on home
If we want to display measured data from the extension (wind, temperature, level...) under the graph on the initial (home page) check the box. If we don't want to display the data from the extension, we uncheck the box.
* Warning: in order for the data to be displayed correctly, it is necessary to have the extension enabled and set correctly.

### Show sensors on home
If we want to display the measured data from the sensors under the graph on the initial (home page), we check the box. If we don't want to display the data from the sensors, we uncheck the box.
* Warning: in order for the data to be displayed correctly, the sensors must be enabled and configured correctly.

### Select Language
By selecting the language, we can change the language used in the web interface.

* Click the down arrow to the right of the language field to display a list of available languages.
* Click on the language you want to use in the interface.
* Click the "Confirm Changes" button at the bottom of the page.

The software restarts and after a few seconds the interface is displayed in the selected language.

### Show pictures at stations
Check this box to display station images on the homepage and stations page.

## Weather Section
The weather section supplies shared forecast data to OSPy and to plug-ins that adjust watering. Every consumer uses the provider selected in Options, so the service does not need to be configured separately in each plug-in.

### Use Weather
Enable or disable weather retrieval from the selected provider.

### Weather provider
**Open-Meteo automatic model** selects a suitable available model without an API key. **CHMI ALADIN via Open-Meteo** requests the ALADIN model where it is available. **Stormglass** preserves the original service and requires its own API key. Open-Meteo is intended for non-commercial use under its service terms and OSPy attributes it beside the forecast.

When an older installation is upgraded, a saved Stormglass key keeps Stormglass selected. Installations without a key migrate to Open-Meteo. During a temporary service failure the last valid data remain visible; OSPy does not silently switch to a different provider.

### Storm Glass API key
Required only when Stormglass is selected as the provider.

### Location
City name or zip code. OpenStreetMap resolves it for the selected weather provider.

Use **Select on map** to open a touch-friendly map, click the exact weather point, and confirm it. **Use device location** can place the marker from the browser after the user grants permission. The selected latitude and longitude become the authoritative weather location after Options are saved; editing the text Location field switches back to OpenStreetMap name search. Below the coordinate status, Home shows three forecast cards for now, approximately +3 and +6 hours with local icons, temperature and precipitation. Details identify the data provider and last update time.

## Users Section
To increase security, we recommend changing the OSPy system password and username from the default "admin". You can also disable the password requirement if needed.

* Click on the triangle to the left of the bar labeled "Users" to expand the section.
* Check the "Disable security" box only if you have a very good reason to disable password and username protection. The system will no longer require user login. All sections will be accessible.
* Enter your username.
* Enter your current password.
* Enter your new password in the fields marked "New Password" and "Confirm Password".
* Click the "Confirm Changes" button at the bottom of the page.

You will be returned to the home page. Your new password and name will be required the next time you log in.

### Disable security
If the box "Disable security" is checked, we allow anonymous users without a password to access the system.

### Username
Enter your username in the text box. This is "admin" on a fresh install.

### Current password
Enter the current password in the text box.

### New password
Enter the new password in the field marked "New password".

### Confirm password
In the field marked "Confirm password", enter the same new password as in the field "New password".

### Aditional users
After clicking the button, a page will open where we can create and possibly edit new users to access the system.

## Security Section

### Form protection
Actions that change settings or system state are in the form token protected web interface. If the page is open for a long time or the browser session times out, reload the page and try again.

### Use HTTPS access
In case we have configured the OSPy server for higher data transfer security using an SSL certificate, check the "Use HTTPS access" box. If the option "Use HTTPS access" is checked and the server is not set correctly, OSPy will start as an unsecured http server.

The server-side HTTPS selection is now explicit: the own certificate has priority, otherwise Let’s Encrypt is used; enabling both options no longer causes a silent HTTP fallback.

### Domain name
The certificate is located on the system in the directory '/etc/letsencrypt/live/' domain name '/fullchain.pem' and '/etc/letsencrypt/live/' domain name '/privkey.pem'. The certificate must be manually installed in the system (Linux) using the "Certbot" tool (the use of https will be reflected in OSPy only after OSPy is restarted).
* The certificate service installation procedure can be found in the help "Readme" file or on GitHub.

### Use HTTPS with Certbot
SSL certificate using Let's Encrypt certificate authority.
Certbot (https://certbot.eff.org/) and Let's Encrypt (https://letsencrypt.org/).

```bash
sudo apt-get install certbot
```

```bash
certbot --version
```

```bash
sudo certbot certonly --standalone -d your_domain_name
```

```bash
sudo certbot renew
```

```bash
sudo cp /etc/letsencrypt/live/your.domain.com/fullchain.pem /home/pi/OSPy/ssl
```

```bash
sudo cp /etc/letsencrypt/live/your.domain.com/privkey.pem /home/pi/OSPy/ssl
```

```bash
sudo service ospy restart
```

### Use Own HTTPS access
If "Use custom HTTPS access" is selected in OSPy settings, you need to put file: fullchain.pem and privkey.pem in ssl directory in OSPy location. Warning: OSPy must be restarted.
```bash
sudo openssl req -new -newkey rsa:4096 -x509 -sha256 -days 3650 -nodes -out fullchain.pem -keyout privkey.pem
```
The second way is to use the "generate" button in the SSL certificate tab.

### API CORS allowed origin
This option sets the `Access-Control-Allow-Origin` header used by the API for clients running in a browser. The value `*` allows any origin, one origin can be specified for example `https://example.com`, multiple origins separated by a comma, or leave the field empty and CORS headers will not be sent. It does not replace API authentication; it only determines which web origins are allowed to read API responses.

### Enable API JSONP
This option enables the legacy `callback` parameter for JSONP API responses. Leave it turned off unless it is required by the old integration. Common API clients are supposed to use JSON with CORS.

### Remembered browser logins
The login page can remember the browser using a long-term random token stored in a secure cookie. OSPy only stores the hash of this token, not the user's password. Use the Cancel button to delete all saved logins in browsers; affected browsers must log in again with a password.

## Sensors Section
The sensor section contains settings for security of sensors.

### Password for uploading
Password for uploading firmware from OSPy to sensor (for all used sensors - the same password must be used in sensor options.)

## Station Handling Section
The "Configure Stations" section contains general settings that affect station scheduling and combining.

### Maximum usage
Specifies how station runs can overlap. `0` means no usage limit, so stations can run simultaneously if their programs overlap. `1` always means one station at a time, if each station has usage `1`. A higher value allows multiple stations to run concurrently, if the sum of their usage does not exceed the set limit.

This setting also affects when the pause between stations is inserted.

#### About Sequential and Concurrent modes
* Sequential mode is mainly used when the water source cannot supply multiple branches at the same time. Example: at Maximum Utilization `1` and Station Utilization `1`, Station 3 must finish before Station 4 can start.
* Concurrent mode is used when a water source can handle multiple branches at once. Example: at Maximum Utilization `0` stations 2, 3 and 4 can run simultaneously if their programs overlap.

### Number of outputs
Total number of outputs available is 8 outputs plus outputs from expansion boards. The number of outputs can be set higher than the actual number of physical outputs, thereby creating virtual outputs.

### Pause between stations
Pause inserted between sequentially started stations when the scheduler cannot start them at the same time, in seconds between 0 and 3600. This does not advance the station relative to the master station.

Example: with Maximum Usage `1` and Station Usage `1`, a value of `30` will start the next station 30 seconds after the end of the previous station.

### Minimum runtime
Skips the pause between stations if the previous run was shorter than this value, in seconds between 0 and 86400.

Example: with pause `30` and minimum run time `10`, a station that only ran for 5 seconds will not force a 30 second pause.

## Configure Master Section
The "Configure Master" section selects master station 1, master station 2, and the time offsets used when master station is activated. The main station is usually a pump or main water supply valve.

The Master Station will only be used for stations that have it set on the Stations page, or for programs that select Master Station 1 or 2 for stations set to "Activate Master 1/2 by Program".

### Master station
Selection of the first master station, such as a pump or master valve.

### Master two station
Selecting a second master station, for example a second pump or another water source.

### Activate relay
If checked, the relay will also be activated as the main output.

### Master start offset
Master station 1 power-on time offset from station start, in seconds between -1800 and +1800. Negative values ​​start the master earlier, positive values ​​later.

Example: `-10` starts the master station 10 seconds before the station. `+10` starts it 10 seconds after the station.

### Master stop offset
Master station 1 shutdown time offset relative to station end, in seconds between -1800 and +1800. Negative values ​​will shut down the main station sooner, positive values ​​will keep it running longer.

Example: `-5` turns off the master station 5 seconds before end of station. `+20` turns it off 20 seconds after the end of the station.

### Master two start offset
Time shift of main station 2 switch-on relative to station start. It works the same as master station start shift, but only for master station 2.

### Master two stop offset
Main station 2 shutdown time offset relative to station end. It works the same as master station shutdown shift, but only for master station 2.

## Rain Sensor Section
Sets the rain sensor switch type. If you are using a Raspberry Pi and want to connect the rain sensor directly to the GPIO pins, use pins 8 and 6 (gnd).

### Use rain sensor
Check the box "Use sensor" to enable rain sensing.

### Normally open
Check the "Normally open" box if the sensor is normally open without rain, otherwise uncheck the box. Refer to the rain sensor user manual for switch type information.

### Set rain delay
When the rain sensor is activated, a rain delay is set (this is suitable, for example, for blocking programs for longer than the rain sensor provides).

### Rain delay time
Rain delay time (in hours), between 0 and 500.

## Logging Section
Turn on run logging and set the number of records you want to keep. Turn on logging of sent emails and set the number of records you want to keep.

### Enable run log
Check the box "Enable run log". This will turn on logging and turn on the watering history on the timeline on the home page. Record all station runs - note that repetitive writing to the SD card may shorten its life.

### Max run entries
Enter the number of entries you want to save in the log. Set a number that covers a reasonable amount of time, such as a week or a month. This will depend on the number of programs and stations you have. There will be one entry each time the station starts. 0 = no limit.

### Enable email log
Check the box "Enable email log". This will turn on logging and enable email watering history.

### Max run entries
Enter the number of entries you want to save in the log. Set a number that covers a reasonable amount of time, such as a week or a month. This will depend on the number of programs and stations you have. There will be one record for each Email. 0 = no limit.

### Enable events log
Enable Event Log (Rain Sensor, Rain Delay, Server, Internet External IP ...)

### Max run entries
Number of event records to save to disk, 0 = no limit.

### Enable debug log
Click "Enable debug log" to save all internal operations in OSPy to a file for better debugging. * Note: * saving data to a file too often can damage the SD card or reduce the capacity of the SD card (storage) after a long time. All operations (including from all extensions) are listed.

## System Restart Section
The "System Restart" section contains buttons to restart the software, to restart the hardware, to turn off the hardware and to clear all settings to default values.

### Restart
The "Restart" button only restarts the software. It is a quick forced way to implement changes in software.

### Reboot
The "Reboot" button reboots the Raspberry Pi. This takes longer but will perform a full system reboot.

### Shutdown
The "Shutdown" button turns off the power to the Raspberry Pi hardware.

### Default
The "Default" button will clear all user settings to a default clean install of OSPy.
* All settings can also be deleted manually in OSPy (we find the ospy/data folder in the system and delete all files in the folder).

## System Backup Section
If we want to backup all the settings of our OSPy irrigation system or transfer the settings to another OSPy system, we use the button "Download" followed by "Upload".

### Download
The "Download" button is used to download a configuration file to the computer for later use or to restore the OSPy system. Not only the database file (options.db) is saved, but also the stations folder where station images are stored. At the same time, the events.log log file (if any) is saved. Everything is stored in a zip file (example: ospy_backup_systemname_4.12.2020_18-40-20.zip). We can easily identify which OSPy system the backup is from. The SSL folder, where the certificate is, is not saved in the backup zip file for security reasons!

### Upload
The Upload button allows you to insert and restore OSPy (for example, when reinstalling Linux). The uploaded file must be a zip file! The following paths and files must be in the file.

```bash
*.zip folder:
ospy-backup.json
ospy/data/default/options.db.*
ospy/data/backup/options.db.*
ospy/data/events.log
ospy/images/stations/station1.png
ospy/images/stations/station1_thumbnail.png
```
Or other station images in the same format.

New backups contain `ospy-backup.json`, which records the backup format, OSPy version, creation time and a SHA-256 checksum and size for every file. The archive contains the OSPy settings database, system event data and station images. SSL private keys, plug-in code and Python caches are intentionally excluded; plug-in data directories remain covered by the separate OSPy package Backup plug-in. Before restoration, OSPy rejects invalid ZIP paths, links, encrypted or duplicate entries, excessive size or compression and any file outside `ospy/data/` and `ospy/images/stations/`. The limits are 50,000 entries and 512 MB expanded size; a file larger than 1 MB may not exceed a 200:1 compression ratio, and the configured upload limit may be lower. Every file is verified against the manifest and extracted to a staging directory. OSPy then creates an automatic pre-restore safety backup and atomically replaces the data before restarting. Older OSPy backups without a manifest remain supported as a legacy data-only format and receive the same ZIP path and size checks.
Active web sessions are neither backed up nor restored; you must sign in again after restoration.
OSPy retains the ten newest system safety backups on the device. They are listed in Options, where a selected archive can be downloaded and then restored with Upload.
A system backup contains credentials and security settings, so downloaded archives must be stored securely.

## SSL Certificate
If we have our own certificate for SSL (https) security (fullchain.pem and privkey.pem) we can upload it here using the form.

## Generate
If we want to generate an SSL certificate, press the "generate" button. A certificate will be generated in the ssl directory. Subsequently, in the settings/security, we check the "own HTTPS" option and then restart OSPy.

### Upload
The "Upload" button sends the attached files (fullchain.pem and privkey.pem) to the ssl folder in the OSPy directory.

----

# Stations page
On the page "Stations page" we set station names, properties around the use of the amount of water, control of the main stations.

## Station
Automatic numbering to mark stations. For example 1 = station 1, 2 = station 2...

## Name
Custom naming of stations for better identification in the system, for example "lawn".

## Usage
Set concurrency (0) or sequence (>=1) for certain stations. More about concurrency or sequence in the text above in the section "Settings / About sequential and concurrent modes".

## Precipitation
The amount of water per hour in mm that will be sprayed by the sprinklers at that station. Used for weather based programs. To measure this value, it is advisable to purchase, for example, a plastic rain gauge.

* Refers to the time required for a given amount of water to infiltrate a specific type of soil. In general, the uptake rate of a lighter textured (sandy) soil is greater than that of a heavier textured (clay) soil. However, sprinkler irrigation with large amounts of water can lead to surface runoff even on sandy soils. The uptake rate of soil under irrigation is affected by many factors such as soil texture, soil structure, compaction, organic matter, stratified soils, soil salts, water quality, sediments in irrigation water, etc.

## Capacity
Amount of water the soil can store above level 0. Used for weather based programs.

* Refers to the amount of soil moisture or water content retained in the soil after the excess water drains and the rate of downward movement is reduced. This usually occurs 2-3 days after rain or irrigation in previous soils with a uniform texture and structure.

## ETo factor
Factor used to multiply ETo factor for weather based programs. Use value above 1 in case of sunny/dry soil, use value below 1 for shaded/wet soil.

* Soil type

Soils have different properties that make them unique. Knowing the type of soil you have will help you determine its strengths and weaknesses. While soil is made up of many elements, the place to start is with your soil type. You only need to monitor the composition of the soil particles. OSPy allows users to specify the soil type for each zone (station), allowing for more accurate and efficient watering calculations. Different soil types react differently to water; clayey soils tend to drain, while loamy soils can hold water for long periods, etc. The amount of water contained in the soil after excess water drains off and the ability of the soil to hold water is referred to as field capacity (measured in inches or millimeters).

### Bottle test
How to find the approximate proportions of sand, silt and clay? This is a simple test that will give you a general idea of ​​the proportions of sand, silt and clay present in the soil. Put 5 cm of soil in the bottle and fill it with water.
Mix the water and soil well, put the bottle aside and do not touch it for an hour. After an hour, the water will become clear and you will see that the larger particles have settled:

- Pieces of organic matter may float on the surface of the water
- There is a layer of clay on top.
If the water is still not clear, it is because some of the finer clays are still mixed with the water
- In the middle is a layer of mud
- There is a layer of sand at the bottom

* Measure the depth of sand, silt and clay and estimate their approximate ratio.

The following three types of particles can make up your soil: clay, sand, and silt. Most soils are a combination of these three particles, but the type of particle that dominates dictates many of the properties of your soil. The ratio of these sizes determines the type of soil: clay, loam, clay loam, silt-loam, etc.

* Ideal soil is 40% sand, 40% silt and 20% clay. This mixture is referred to as clay. This takes the best of each type of soil particle. It has good water drainage and allows air to penetrate the soil like sand, but it also retains moisture well and is fertile like silt and clay.

## Balance adjustment
Increase or decrease water balance for weather based programs (if not set to 0).

## Connected
If we have a station connected (it is physically connected) and we want to use it (it can be seen in the selection in programs, on the home page...), we check "Connected". If we do not use the station and do not want to publish it in the OSPy system, we leave "Connected" unchecked. If a station is used as "main station" or "2 main stations" in the system, it cannot be checked or unchecked (deactivated) in the table.
The master station is assigned in the system settings "Settings / master station settings".

## Ignore Rain
If we check "Ignore Rain" for a certain station, the station will be activated according to the program regardless of whether a rain delay is set or whether the rain sensor detects rain. We will use this option, for example, in a greenhouse where it does not rain and we need to water it regularly. or, for example, to start the filtration of the swimming pool, which we also clean regardless of whether it rains.

## Activate Master?
### None
No master station will be used (if a certain station is activated, the master station will not be activated).
### Activate Master
If we require that when a certain station is activated, the main station is also activated (for example, a pump or main valve with water), select the item "ON main?".
### Activate Master Two
If we require that when a certain station is activated, the second main station is also activated (for example, a second pump or another water source), select the item "ON main 2?".
### Activate Master 1/2 by program
If we want to activate the main station or the second main station, we select the item "Activate Master 1/2 by program" by the program. For the program it is then possible to choose which master station is to be used for this station (example: program 1 controls stations 1-4 and master station 5. Program 2 controls stations 1-4 and the second master station 6).

## Notes
Notes are used for operating the OSPy system. For example, it can be noted: what type of el. valve, sprinkler, etc. we have used in the system.

## Image
After clicking on the window, a page opens where you can upload your own image to the station.

----

# Sensors page
On the "Sensors page" page, we can add or delete sensors that perform different functions in the OSPy system. OSPy currently supports sensors from pihrt.com and shelly.com.

## Add a New Sensor
The "Add a New Sensor" button will add a new sensor to the system. Sensor settings are listed below in the "Sensor Parameters" section.

## Sensor Parameters
Two types of communication are used for sensors:
* Wireless (radio) - ID radio sensor
* Network (Wi-Fi/LAN) - MAC address, IP address
You can choose from different types of sensors:
* Dry Contact
* Leak Detector
* Moisture
* Motion
* Temperature
* Multi sensor contact
* Multisensor leak detector
* Multi sensor humidity
* Multisensor motion
* Multisensor temperature
* Multisensor ultrasound
* Multi-sensor soil moisture

### Enable sensor
Enable or disable this sensor.

### Sensor name
Enter the sensor name. Sensor names must be non-zero and unique.

### Sensor type
Select the sensor type.

#### Dry Contact
* Open program(s) Check the desired programs to run.
* Or stop these running stations in the scheduler.
* Closed program(s) Mark the desired programs to run.
* Or stop these running stations in the scheduler.

#### Leak Detector
* Sensitivity (0-100%) Exceeding this level activates the high program(s).
* Stabilization time (mm:ss) After this set time, the detector will not react to a change.
* Low Program(s) Mark the desired programs to run.
* High Program(s) Mark the desired programs to run.

#### Moisture
* Low Level (0-100%) Exceeding this level activates the low program(s).
* Low Program(s) Mark the desired programs to run.
* High level (0-100%) When this level is exceeded, the high program(s) will be activated.
* High Program(s) Mark the desired programs to run.

#### Motion
* Program(s) Select the desired programs to run.

#### Temperature
* Low level (0-100 °C/°F) When this level is exceeded, the low program(s) will be activated.
* Low Program(s) Mark the desired programs to run.
* High level (0-100 °C/°F) When this level is exceeded, the high program(s) will be activated.
* High Program(s) Mark the desired programs to run.
For the temperature, degrees Celsius or degrees Fahrenheit are displayed, depending on how we have set the temperature on the title page (bottom right) (you can change the units by clicking on the temperature).

#### Ultrasonic
* Distance from the ultrasonic sensor (top) to the minimum water level in the tank.
* Distance from the ultrasonic sensor (top) to the maximum water level in the tank.
* The minimum water level in the tank (from the bottom of the tank) for the report.
* Cylinder diameter for volume calculation.
* Display in liters or m3.
* Stop stations if minimum water level.
* Delay time (hours).
* Stop stations if the ultrasonic sensor has a fault.
* Stop these stations in the scheduler.
* Maximum water level regulation.
* Maximum maintained water level.
* Maximum running time in activation.
* Minimum maintained water level.
* Output for regulation.

#### Soil Moisture
* Probe xx controls the program (select the program you want to influence with probe 1-16 in the list of programs).
* Calibrate xx probe for 100% (enter the voltage level in volts to calibrate the probe at 100% humidity).
* Calibrate xx probe for 0% (enter the voltage level in volts to calibrate the probe at 0% humidity).

### Type of communication
Select communication type for sensor.
#### Radio
Enter the sensor ID for your radio sensor. The sensor ID must be non-zero and unique.

#### Wi-Fi/LAN
* Enter the MAC address of the sensor. Example: aa: bb: cc: dd: ee: ff
* Enter the IP address of the sensor. Example: 192.168.88.10

### Sample Rate
Enter the sampling time in minutes and seconds (mm:ss).

### Log Samples
Enable sample logging.

### Log Events
Enable event logging.

### Text/Email Events
Enable sending Emails when an event occurs. The email notification extension is required for this feature!

### Notes
Here we can make our notes.

## Delete All sensors
The "Delete All sensors" button will delete all added sensors in the system.

----

## Add new sensor (from shelly.com)
Shelly sensors can be integrated into OSPy using the "shelly cloud integrator" extension in which we connect available devices (either via the shelly.com cloud or in the local network).
We can then search for these devices in OSPy in the sensor/search section. In OSPy, we can use measurements of, for example, consumption, voltage, output status, etc.

----

#  Help page
On the page "Help page" we find documentation for all extensions, system OSPs, system changes, API access, web interface.

## OSPy
### Readme
Main OSPy documentation, system installation, board connections, licenses.

### Changelog
Changes in the OSPy system or in extensions

### Programs
Internally, all programs maintain a schedule that can be edited directly (just like a custom program).
The following types of programs have been created for easier handling.
Each program can be one of these types. Finally, each program can also be written as a custom program.<br/>

Prog/type_data  |             0                |     1          |      2         |     3         |      4         |     5
             --:|:--                           |:--             |:--             |:--            |:--             |
DAYS_SIMPLE     |start_time                    |duration        |repeat pause    |repeat times   |list days to run|
REPEAT_SIMPLE   |start_time                    |duration        |repeat pause    |repeat times   |repeat days     |start_date
DAYS_ADVANCED   |list of intervals [start, end]|list days to run|                |               |                |
REPEAT_ADVANCED |list of intervals [start, end]|repeat days     |                |               |                |
WEEKLY_ADVANCED |list of intervals [start, end]|                |                |               |                |
CUSTOM          |list of intervals [start, end]|                |                |               |                |
WEEKLY_WEATHER  |                              |                |                |               |                |

set_days_simple start_min, duration_min, pause_min, repeat_times, [days]
set_repeat_simple start_min, duration_min, pause_min, repeat_times, repeat_days, start_date
set_days_advanced [schedule], [days]
set_repeat_advanced [schedule], repeat_days, start_date
set_weekly_advanced [schedule]
set_weekly_weather  irrigation_min, irrigation_max, run_max, pause_min, pems

### Web Interface Guide - Czech
Help for the web interface in Czech.

### Web Interface Guide - English
Web interface help in English.

### Web Interface Guide - German
Web interface help in German.

### Web Interface Guide - Polish
Web interface help in Polish.

### Web Interface Guide - Russian
Web interface help in Russian.

### Web Interface Guide - Serbian
Web interface help in Serbian.

### Web Interface Guide - Slovak
Help for the web interface in Slovak.

## API
### Readme
For modern web browsers, it is recommended that the API be built on the CRUD principle using JSON as the data container format.

### Details
HTTP/s method mapping.

## Plug-ins
The basic structure of all extensions is as follows:

plugins
+ plugin_name
  + data
  + docs
  + static
  + script
  + templates
  + __init__.py
  \ README.md

Static files will be automatically made available at the following location: /plugins/plugin_name/static/...
All * .md files in the docs directory will be visible on the "Help page" page. *

### Available Extensions:

* Usage Statistics (anonymous statistics about OSPy system usage)
* LCD Display (16x2 character LCD display connected via I2C bus)
* Pressure Monitor (monitoring the pressure in the pipeline - pump protection)
* Voice Notification (sound notifications - playing mp3 files)
* Pulse Output Test (output test - used to find a certain valve in the ground)
* Button Control (controlling the OSPy system using 8 buttons - used for manually starting programs)
* CLI Control (remote control of peripherals using URL commands - for example RF sockets)
* System Watchdog (Raspberry Pi system watchdog, if the system freezes, the system will restart)
* Voltage and Temperature Monitor (measurement of voltage and temperature using the I2C bus)
* Remote Notifications (sending data to a remote server using PHP)
* System Information (OSPy and Linux system information)
* Air Temperature and Humidity Monitor (measurement of temperature 6x DS18B20 and humidity DHT11 using I2C bus)
* Wind Speed Monitor (wind speed measurement using I2C bus)
* Weather-based Rain Delay
* Relay Test (tests the relay for the main pump)
* UPS Monitor (monitors system power failure, sends email and shuts down Linux system)
* Water Consumption Counter (virtual water flow meter based on main station run calculation)
* SMS Modem (remote control via SMS and USB modem)
* Signaling Examples (example of "signal" notifications in the OSPy system)
* E-mail Notifications (sending E-mails from the system - some other extensions also use this extension, for example: Wind Speed Monitor, Pressure Monitor, Air Temperature and Humidity Monitor...)
* Remote FTP Control (simplified remote control of OSPy using a server with PHP and FTP)
* System Update (use this extension to easily update the OSPy system from GIThub instead of system commands)
* Water Meter (flow measurement using a water meter with pulse output using the I2C bus)
* Webcam Monitor (takes photos from USB webcam)
* Weather-based Water Level Netatmo (setting the amount of water for irrigation from the Netatmo weather station)
* Direct 16 Relay Outputs (using this extension we can control 16 relays (stations) connected directly to the Raspberry Pi, but some other extensions will not be available)
* MQTT (OSPy status reporting using the MQTT protocol, station control via MQTT...)
* system debug information
* Weather-based Water Level (setting the amount of water for irrigation based on the weather forecast)
* Real Time and NTP time (extension that sets system time - Linux and HW RTC time from NTP server, HW RTC uses I2C bus)
* Water Tank (water level measurement using ultrasound - for example in a well using I2C bus)
* Monthly Water Level (setting the amount of water for individual months)
* Pressurizer (pressurizing the pump before starting programs)
* Ping monitor (measuring network outages)
* Temperature Switch (temperature regulator that allows 3 independent zones)
* Pool Heating (pool temperature regulation according to solar heating)
* E-mail reader (control of OSPy using E-mail messages)
* Weather Stations (display values from other extensions in the style of clock hands) version 1.0
* Telegram Bot (communicate with OSPy using telegram.org app)
* Door Opening (opening the door lock or sliding gate)
* Voice Station (sound notifications based on station events - playback of wav and mp3 files)
* Blinds control (this extension sends examples via REST API to Wi-Fi relays from Shelly or similar relays)
* Internet connection speed monitor (response, download, upload)
* E-mail Notifications SSL (sending E-mails from the system - some other extensions also use this extension, for example: Wind Speed ​​Monitor, Pressure Monitor, Air Temperature and Humidity Monitor...) This extension is a more modern variant of the original extension E-mail Notifications (Connection via SSL layer).
* Sunrise and Sunset (calculation of astronomical data such as sunrise and sunset. According to these calculations, it allows programs to be run subsequently).
* PV boiler (boiler heating from the distribution network or PV power plant).
* IP cameras (allows monitoring from IP cameras. As JPEG preview, or GIF image, or MJPEG stream from the camera).
* CHMI (allows you to read the current weather from the CHMI weather radar and set the time delay according to it. At the same time, display the RGB weather status on the HW map).
* Therefore (the default plugin for creating other new plugins. The plugin doesn't do anything fancy, but explains how it works).
* Label Maker (creation of EAN and QR codes).
* IP Scanner (search for IP and MAC in the network).
* Database Connector (connection to the database for storing data from sensors).
* OSPy Backup (data directory backup from all extensions to zip files).
* MQTT Home Assistant (integration into HASS using MQTT).
* Shelly Cloud Integration (retrieving states from the Shelly device manufacturer's cloud).
* Current Loop Tanks Mmonitor (level measurement from 4 sensors).
* Network Ping Monitor (monitoring the availability of 3 devices in the network).
* Weather Dashboard (display values from other extensions in the style of clock hands) version 2.0
* Thermostat
----

# Logging out
After clicking the "Logging out" button, the user logs out of the system.
