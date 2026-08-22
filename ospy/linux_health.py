"""Passive, failure-contained Linux and root-storage health diagnostics."""

import datetime
import os
import platform
import re
import shutil
import subprocess
import tempfile
import time
from pathlib import Path
from threading import RLock, Thread


REFRESH_SECONDS = 600
COMMAND_TIMEOUT = 5
JOURNAL_LINES = 2000
_lock = RLock()
_refreshing = False
_cache = {
    'status': 'unknown',
    'summary': _('Linux and storage checks have not run yet.'),
    'details': '',
    'solution': '',
    'updated': 0,
}


def _run(command, timeout=COMMAND_TIMEOUT):
    """Run one fixed read-only command without a shell."""
    try:
        environment = os.environ.copy()
        environment['LC_ALL'] = 'C'
        result = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            encoding='utf-8',
            errors='replace',
            timeout=timeout,
            check=False,
            env=environment,
        )
        return result.returncode, result.stdout.strip(), result.stderr.strip()
    except FileNotFoundError:
        return 127, '', _('Command is not installed') + ': ' + command[0]
    except subprocess.TimeoutExpired:
        return 124, '', _('Command timed out') + ': ' + command[0]
    except Exception as error:
        return 1, '', '{}: {}'.format(type(error).__name__, error)


def _human_bytes(value):
    try:
        number = float(value)
    except (TypeError, ValueError, OverflowError):
        return '-'
    units = ('B', 'KB', 'MB', 'GB', 'TB')
    for unit in units:
        if number < 1024.0 or unit == units[-1]:
            return '{:.1f} {}'.format(number, unit)
        number /= 1024.0
    return '-'


def _root_mount():
    """Read the root mount directly from procfs without invoking mount tools."""
    try:
        with open('/proc/self/mountinfo', 'r', encoding='utf-8',
                  errors='replace') as source:
            for line in source:
                parts = line.split()
                if len(parts) < 10 or parts[4] != '/':
                    continue
                separator = parts.index('-')
                return {
                    'source': parts[separator + 2],
                    'fstype': parts[separator + 1],
                    'options': set(parts[5].split(',')),
                }
    except (OSError, ValueError, IndexError):
        return None
    return None


def _parent_device(source):
    if not source or not source.startswith('/dev/'):
        return ''
    try:
        source = os.path.realpath(source)
    except OSError:
        pass
    name = os.path.basename(source)
    if re.match(r'^mmcblk\d+p\d+$', name):
        name = re.sub(r'p\d+$', '', name)
    elif re.match(r'^nvme\d+n\d+p\d+$', name):
        name = re.sub(r'p\d+$', '', name)
    elif re.match(r'^[a-z]+\d+$', name):
        name = re.sub(r'\d+$', '', name)
    return '/dev/' + name


def _storage_identity(device):
    if not device:
        return ''
    base = os.path.basename(device)
    device_path = Path('/sys/block') / base / 'device'
    values = []
    labels = (
        ('name', _('name')), ('type', _('type')), ('serial', _('serial')),
    )
    for filename, label in labels:
        try:
            value = (device_path / filename).read_text(
                encoding='utf-8', errors='replace').strip()
            if value:
                values.append('{}: {}'.format(label, value))
        except OSError:
            pass
    try:
        sectors = int((Path('/sys/block') / base / 'size').read_text(
            encoding='ascii', errors='replace').strip())
        values.append('{}: {}'.format(_('capacity'), _human_bytes(sectors * 512)))
    except (OSError, TypeError, ValueError):
        pass
    return '{}{}'.format(device, '; ' + '; '.join(values) if values else '')


def _write_probe(directory):
    """Write, fsync, read and remove a tiny file in the OSPy data directory."""
    descriptor = None
    filename = ''
    payload = ('OSPy Linux health {}\n'.format(time.time())).encode('ascii')
    try:
        descriptor, filename = tempfile.mkstemp(
            prefix='.linux-health-', dir=directory)
        with os.fdopen(descriptor, 'wb') as output:
            descriptor = None
            output.write(payload)
            output.flush()
            os.fsync(output.fileno())
        with open(filename, 'rb') as source:
            if source.read(len(payload) + 1) != payload:
                return False, _('Written and read test data do not match.')
        return True, _('Write, sync and read test passed.')
    except Exception as error:
        return False, '{}: {}'.format(type(error).__name__, error)
    finally:
        if descriptor is not None:
            try:
                os.close(descriptor)
            except OSError:
                pass
        if filename:
            try:
                os.unlink(filename)
            except OSError:
                pass


def _ext4_metadata(source, fstype):
    if fstype != 'ext4' or not source or not source.startswith('/dev/'):
        return {}, ''
    if not shutil.which('tune2fs'):
        return {}, _('tune2fs is not installed.')
    code, output, error = _run(['tune2fs', '-l', source])
    if code != 0:
        return {}, error or output or _('EXT4 metadata is not accessible.')
    values = {}
    for line in output.splitlines():
        if ':' in line:
            key, value = line.split(':', 1)
            values[key.strip()] = value.strip()
    return values, ''


def _journal(command):
    code, output, error = _run(command)
    return (output, '') if code == 0 else ('', error or output)


def _kernel_messages():
    if shutil.which('journalctl'):
        output, error = _journal([
            'journalctl', '-k', '--no-pager', '--since', '30 days ago',
            '-n', str(JOURNAL_LINES), '-o', 'short-iso',
        ])
        if output:
            return output, 'journalctl', ''
    else:
        error = _('journalctl is not installed.')
    if shutil.which('dmesg'):
        code, output, dmesg_error = _run(['dmesg', '--color=never'])
        if code == 0 and output:
            return output, 'dmesg', ''
        error = dmesg_error or error
    return '', '', error or _('Kernel messages are not accessible.')


def _system_messages():
    if not shutil.which('journalctl'):
        return '', _('journalctl is not installed.')
    return _journal([
        'journalctl', '-b', '--no-pager', '-n', '1000', '-o', 'short-iso',
    ])


def _matching_lines(text, patterns, limit=5):
    matches = []
    seen = set()
    for line in text.splitlines():
        if any(re.search(pattern, line, re.IGNORECASE) for pattern in patterns):
            normalized = re.sub(r'^\[[^]]+\]\s*', '', line).strip()
            if normalized and normalized not in seen:
                seen.add(normalized)
                matches.append(normalized[:500])
    return matches[-limit:]


def _power_status():
    if not shutil.which('vcgencmd'):
        return 'unknown', _('Raspberry Pi throttling information is unavailable.')
    code, output, error = _run(['vcgencmd', 'get_throttled'], timeout=3)
    match = re.search(r'0x([0-9a-fA-F]+)', output)
    if code != 0 or not match:
        return 'unknown', error or output or _('Raspberry Pi power status could not be read.')
    value = int(match.group(1), 16)
    if value & 0xF:
        return 'error', '{}; {}'.format(
            output, _('Undervoltage or throttling is active.'))
    if value & 0xF0000:
        return 'warning', '{}; {}'.format(
            output, _('Undervoltage or throttling occurred previously.'))
    return 'ok', '{}; {}'.format(
        output, _('No undervoltage or throttling was detected.'))


def _cpu_temperature():
    paths = [Path('/sys/class/thermal/thermal_zone0/temp')]
    for path in paths:
        try:
            value = float(path.read_text(encoding='ascii').strip())
            value = value / 1000.0 if value > 1000 else value
            if value >= 85:
                return 'error', value
            if value >= 75:
                return 'warning', value
            return 'ok', value
        except (OSError, TypeError, ValueError):
            pass
    return 'unknown', None


def _memory_usage():
    values = {}
    try:
        with open('/proc/meminfo', 'r', encoding='ascii',
                  errors='replace') as source:
            for line in source:
                if ':' not in line:
                    continue
                key, value = line.split(':', 1)
                match = re.search(r'(\d+)', value)
                if match:
                    values[key] = int(match.group(1)) * 1024
    except OSError:
        return 'unknown', None, None
    total = values.get('MemTotal')
    available = values.get('MemAvailable')
    if not total or available is None:
        return 'unknown', None, None
    percent = max(0.0, min(100.0, (total - available) * 100.0 / total))
    status = 'error' if percent >= 95 else 'warning' if percent >= 85 else 'ok'
    return status, percent, available


def _load_average():
    try:
        load1, load5, load15 = os.getloadavg()
        processors = os.cpu_count() or 1
        normalized1 = load1 / processors
        normalized5 = load5 / processors
        status = (
            'error' if normalized1 >= 2.0 and normalized5 >= 1.5 else
            'warning' if normalized1 >= 1.25 or normalized5 >= 1.0 else 'ok'
        )
        return status, (load1, load5, load15, processors)
    except (AttributeError, OSError):
        return 'unknown', None


def _failed_units():
    if not shutil.which('systemctl'):
        return [], _('systemctl is not installed.')
    code, output, error = _run([
        'systemctl', '--failed', '--no-legend', '--plain', '--no-pager',
    ])
    if code not in (0, 1):
        return [], error or output
    units = []
    for line in output.splitlines():
        parts = line.split()
        if parts:
            units.append(parts[0])
    return units[:20], ''


def _record(records, status, label, message):
    records.append({'status': status, 'label': label, 'message': message})


def _collect_linux_health():
    """Perform bounded checks. Every optional check fails independently."""
    if platform.system().lower() != 'linux':
        return {
            'status': 'unknown',
            'summary': _('Operating system health checks are available only on Linux.'),
            'details': _('Current platform') + ': ' + platform.system(),
            'solution': '', 'updated': time.time(),
        }

    records = []
    mount = _root_mount()
    root_source = mount.get('source', '') if mount else ''
    root_fstype = mount.get('fstype', '') if mount else ''
    if not mount:
        _record(records, 'warning', _('Root filesystem'),
                _('Root filesystem information could not be read.'))
    elif 'ro' in mount['options'] or 'rw' not in mount['options']:
        _record(records, 'error', _('Root filesystem'), '{} ({}, {})'.format(
            root_source or '-', root_fstype or '-', _('read-only')))
    else:
        _record(records, 'ok', _('Root filesystem'), '{} ({}, {})'.format(
            root_source or '-', root_fstype or '-', _('read-write')))

    try:
        usage = shutil.disk_usage('/')
        used_percent = usage.used * 100.0 / usage.total if usage.total else 0.0
        status = ('error' if used_percent >= 95 else
                  'warning' if used_percent >= 85 else 'ok')
        _record(records, status, _('Disk space'),
                '{}: {:.1f} %; {}: {}'.format(
                    _('used'), used_percent, _('free'), _human_bytes(usage.free)))
    except Exception as error:
        _record(records, 'warning', _('Disk space'),
                '{}: {}'.format(type(error).__name__, error))

    try:
        stat = os.statvfs('/')
        used_inodes = stat.f_files - stat.f_ffree
        inode_percent = (used_inodes * 100.0 / stat.f_files
                         if stat.f_files else 0.0)
        status = ('error' if inode_percent >= 95 else
                  'warning' if inode_percent >= 85 else 'ok')
        _record(records, status, _('Inodes'),
                '{}: {:.1f} %; {}: {}'.format(
                    _('used'), inode_percent, _('free'), stat.f_ffree))
    except Exception as error:
        _record(records, 'warning', _('Inodes'),
                '{}: {}'.format(type(error).__name__, error))

    data_directory = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
    write_ok, write_message = _write_probe(data_directory)
    _record(records, 'ok' if write_ok else 'error', _('Write test'), write_message)

    metadata, metadata_error = _ext4_metadata(root_source, root_fstype)
    if metadata:
        filesystem_state = metadata.get('Filesystem state', _('unknown'))
        metadata_status = ('ok' if filesystem_state.lower() == 'clean' else
                           'error' if 'error' in filesystem_state.lower() else
                           'warning')
        metadata_parts = [_('state') + ': ' + filesystem_state]
        for key, label in (
                ('Last checked', _('last checked')),
                ('Lifetime writes', _('lifetime writes')),
                ('Mount count', _('mount count'))):
            if metadata.get(key):
                metadata_parts.append(label + ': ' + metadata[key])
        _record(records, metadata_status, _('EXT4 metadata'),
                '; '.join(metadata_parts))
    elif root_fstype == 'ext4':
        _record(records, 'unknown', _('EXT4 metadata'),
                metadata_error or _('Not available without additional permissions.'))

    device = _parent_device(root_source)
    identity = _storage_identity(device)
    if identity:
        _record(records, 'ok', _('Storage device'), identity)

    power_status, power_message = _power_status()
    _record(records, power_status, _('Raspberry Pi power'), power_message)

    temperature_status, temperature = _cpu_temperature()
    if temperature is not None:
        _record(records, temperature_status, _('CPU temperature'),
                '{:.1f} °C'.format(temperature))

    memory_status, memory_percent, memory_available = _memory_usage()
    if memory_percent is not None:
        _record(records, memory_status, _('Memory'),
                '{}: {:.1f} %; {}: {}'.format(
                    _('used'), memory_percent, _('available'),
                    _human_bytes(memory_available)))

    load_status, load_values = _load_average()
    if load_values:
        _record(records, load_status, _('Load average'),
                '{:.2f}, {:.2f}, {:.2f}; {}: {}'.format(
                    load_values[0], load_values[1], load_values[2],
                    _('CPU cores'), load_values[3]))

    failed_units, units_error = _failed_units()
    if failed_units:
        _record(records, 'warning', _('systemd services'),
                '{}: {}'.format(_('failed'), ', '.join(failed_units)))
    elif units_error:
        _record(records, 'unknown', _('systemd services'), units_error)
    else:
        _record(records, 'ok', _('systemd services'), _('No failed units.'))

    kernel_log, kernel_source, kernel_error = _kernel_messages()
    if not kernel_log:
        _record(records, 'warning', _('Kernel log'),
                kernel_error or _('Kernel messages are not accessible.'))
    else:
        storage_errors = _matching_lines(kernel_log, (
            r'\bmmc(?:blk)?\w*.*\b(error|timeout|failed|failure)\b',
            r'Buffer I/O error', r'blk_update_request.*I/O error',
            r'EXT4-fs.*\berror\b', r'JBD2.*\berror\b',
            r'journal.*I/O error', r'remount.*read-only',
            r'metadata I/O error', r'failed to write.*mmc',
        ))
        storage_warnings = _matching_lines(kernel_log, (
            r'EXT4-fs.*\bwarning\b', r'mmc.*CRC', r'mmc.*reset',
        ))
        stability_errors = _matching_lines(kernel_log, (
            r'Kernel panic', r'not syncing: Fatal',
            r'BUG: unable to handle kernel', r'watchdog: BUG: soft lockup',
            r'hard LOCKUP', r'rcu.*stall',
        ))
        stability_warnings = _matching_lines(kernel_log, (
            r'Out of memory:', r'oom-killer', r'Killed process .* total-vm:',
            r'segfault at ', r'general protection fault',
            r'task .* blocked for more than',
        ))
        if storage_errors:
            _record(records, 'error', _('SD card and filesystem log'),
                    '{}: {}'.format(_('critical events'),
                                    ' | '.join(storage_errors)))
        elif storage_warnings:
            _record(records, 'warning', _('SD card and filesystem log'),
                    '{}: {}'.format(_('warnings'),
                                    ' | '.join(storage_warnings)))
        else:
            _record(records, 'ok', _('SD card and filesystem log'),
                    _('No typical MMC, I/O, EXT4 or read-only remount errors were found.'))
        if stability_errors:
            _record(records, 'error', _('Kernel stability'),
                    ' | '.join(stability_errors))
        elif stability_warnings:
            _record(records, 'warning', _('Kernel stability'),
                    ' | '.join(stability_warnings))
        else:
            _record(records, 'ok', _('Kernel stability'),
                    _('No kernel panic, lockup or out-of-memory event was found.'))
        recovery = _matching_lines(kernel_log, (
            r'recovery required on readonly filesystem',
            r'orphan cleanup on readonly fs', r'orphan inodes deleted',
            r'recovery complete',
        ))
        if recovery:
            recovery_complete = any(
                'recovery complete' in line.lower() for line in recovery)
            _record(records, 'unknown' if recovery_complete else 'warning',
                    _('EXT4 recovery at boot'), ' | '.join(recovery))
        _record(records, 'ok', _('Kernel log source'), kernel_source)

    system_log, unused_error = _system_messages()
    if system_log:
        unclean = _matching_lines(system_log, (
            r'system\.journal corrupted or uncleanly shut down',
            r'journal file.*corrupt', r'uncleanly shut down',
            r'journal.*corrupt',
        ))
        if unclean:
            _record(records, 'unknown', _('System journal'),
                    ' | '.join(unclean))

    errors = [item for item in records if item['status'] == 'error']
    warnings = [item for item in records if item['status'] == 'warning']
    if errors:
        status = 'error'
        summary = _('Critical') + ': ' + _(
            'Linux or root storage needs immediate attention.') + ' ' + (
            '{}: {}; {}: {}.'.format(
                _('Errors'), len(errors), _('Warnings'), len(warnings)))
        solution = _(
            'Create a backup immediately. Check the listed power, MMC, I/O and EXT4 errors. '
            'Shut the device down cleanly before removing the SD card. Never run a forced '
            'filesystem check on the mounted root filesystem; check it offline from another Linux system.'
        )
    elif warnings:
        status = 'warning'
        summary = _('Warning') + ': ' + _(
            'Linux and storage checks found items that need attention.') + ' ' + (
            '{}: {}.'.format(_('Warnings'), len(warnings)))
        solution = _(
            'Review the listed checks, failed services and Raspberry Pi power status. '
            'Back up the system if MMC, I/O or EXT4 warnings repeat.'
        )
    else:
        status = 'ok'
        summary = _('OK') + ': ' + _(
            'No signs of Linux, filesystem or SD card failure were found.')
        solution = ''

    status_labels = {
        'ok': _('OK'),
        'warning': _('Warning'),
        'error': _('Critical'),
        'unknown': _('Information'),
    }
    details = '; '.join(
        '[{}] {}: {}'.format(
            status_labels.get(item['status'], _('Information')),
            item['label'], item['message'])
        for item in records
    )
    return {
        'status': status, 'summary': summary, 'details': details,
        'solution': solution, 'updated': time.time(),
    }


def _refresh():
    global _cache, _refreshing
    try:
        result = _collect_linux_health()
    except Exception as error:
        result = {
            'status': 'unknown',
            'summary': _('Operating system health check failed safely.'),
            'details': '{}: {}'.format(type(error).__name__, error),
            'solution': _('Check the OSPy event log and operating system permissions.'),
            'updated': time.time(),
        }
    with _lock:
        _cache = result
        _refreshing = False


def snapshot(force=False):
    """Return cached health immediately and refresh stale data in the background."""
    global _refreshing
    now = time.time()
    with _lock:
        stale = force or now - float(_cache.get('updated', 0) or 0) >= REFRESH_SECONDS
        if stale and not _refreshing:
            _refreshing = True
            worker = Thread(target=_refresh, name='OSPy Linux health')
            worker.daemon = True
            worker.start()
        result = dict(_cache)
        if not result.get('updated') and _refreshing:
            result['summary'] = _('Linux and storage checks are running.')
        return result
