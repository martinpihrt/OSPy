OSPy automated tests
====

Run the core tests from the OSPy root directory:

```bash
python3 -m unittest discover -s tests -v
```

The suite checks:

* compilation of every core web.py HTML template;
* completeness and execution of the documented `pygettext.py` command;
* protection of the repository POT file during the extraction test;
* manifest parser acceptance and rejection rules;
* every `plugin.json` found in the installed OSPy `plugins` directory;
* archive installation blocking before file writes for missing, invalid or
  incompatible manifests;
* partial bulk installation, compatibility warnings and automatic-update
  blocking;
* rejection of unsafe, damaged, encrypted, duplicate, symbolic-link,
  oversized, excessive-entry and excessive-ratio plug-in ZIP archives;
* atomic plug-in replacement, preservation of plug-in `data`, and restoration
  of the previous version after a failed swap or start;
* scheduler behavior for rain delay, manual run-once priority, station order,
  sequential and parallel output usage, station delay, disabled stations and
  program-group postponement;
* shift-register output writes, invalid-index protection, disabled-station
  blocking, primary and secondary master relays, master delays, immediate
  stop-all behavior and scheduler recovery after an output exception;
* sensor offline timeouts, valid-packet recovery, MAC-based recovery after a
  lost or DHCP-changed IP address, malformed-packet isolation, legacy IP-address
  and regulation-output migration, Sensors page rendering, weather request
  timeouts, location retry, coordinate preservation, response validation and
  fallback to the last valid cached weather value;
* non-blocking external-IP cache refresh without duplicate refresh workers;
* cooperative shutdown of scheduler, sensor, weather and plug-in update workers,
  immediate output and master-relay safety, bounded core shutdown ordering and
  synchronous persistence of pending settings;
* API Basic authentication, brute-force locking, security-event throttling,
  role permissions, optional CSRF enforcement and audited station/run-once
  state changes;
* loading older settings databases, adding new defaults, date conversion,
  immediate persistence, reload, fallback to a valid database copy, rejection
  of invalid core values and safe handling of damaged object, log and session
  records;
* the complete plug-in lifecycle: install, activate, health report, restart,
  update, preserved data, failed-start rollback and disable;
* required and optional plug-in dependencies, including manifest validation,
  missing or disabled providers, provider-first startup, consumer-first shutdown
  and cycle rejection;
* system backup manifests, checksums, permitted content, exclusion of active web
  sessions, legacy archive staging, rejection of tampered, undeclared, duplicate
  and traversal entries, invalidation of the restore request session before
  shutdown, atomic restoration and recovery of the previous data after a failed swap;
* System Update channel selection, including stable `master` as the default,
  fixed `beta` selection, repository checks against the selected branch and a
  required safety backup before an update installs the selected branch;
* branch-aware version formatting: `master` keeps the numeric version while
  the `beta` branch adds a `-beta` suffix without changing its revision number;
* real web.py route dispatch and rendering for the main administrator pages,
  plug-in management and installation, anonymous login redirects, role
  protection, Diagnostics JSON success and failure responses, history and
  cache headers, and CSRF rejection before an administrator POST handler runs.

Tests share a temporary OSPy data directory and disable background plug-in
repository checks. Scheduler, API and plug-in dependencies are isolated or
replaced with deterministic in-memory test objects. The suite can therefore run
while the OSPy service is active without opening its options database, starting
update checks, accessing weather services, changing real programs or touching
GPIO.

To additionally compile all plug-in templates and require and validate a
manifest for every plug-in in the separate official OSPy-plugins repository,
provide its `plugins` directory:

```bash
OSPY_PLUGIN_ROOTS=/path/to/OSPy-plugins/plugins python3 -m unittest discover -s tests -v
```

Multiple plug-in roots can be separated with the operating system path
separator (`:` on Linux, `;` on Windows).

GitHub Actions runs the same suite automatically for pushes and pull requests
to the `beta` and `master` branches. The workflow uses Python 3.11, checks out
the official OSPy-plugins repository, and can also be started manually from the
repository **Actions** page. It does not connect to a running OSPy installation
or to irrigation hardware.
