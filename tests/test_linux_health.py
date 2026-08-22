import unittest
from types import SimpleNamespace
from unittest import mock

from tests.test_support import TEST_DATA_DIR  # noqa: F401 - initializes isolation
from ospy import i18n  # noqa: F401 - installs gettext
from ospy import linux_health


class LinuxHealthTests(unittest.TestCase):
    def _common_patches(self):
        return (
            mock.patch.object(linux_health.platform, 'system', return_value='Linux'),
            mock.patch.object(linux_health, '_root_mount', return_value={
                'source': '/dev/mmcblk0p2', 'fstype': 'ext4',
                'options': {'rw', 'relatime'},
            }),
            mock.patch.object(linux_health.shutil, 'disk_usage', return_value=
                              SimpleNamespace(total=1000, used=300, free=700)),
            mock.patch.object(linux_health.os, 'statvfs', create=True,
                              return_value=SimpleNamespace(
                                  f_files=1000, f_ffree=800)),
            mock.patch.object(linux_health, '_write_probe', return_value=
                              (True, 'write passed')),
            mock.patch.object(linux_health, '_ext4_metadata', return_value=({
                'Filesystem state': 'clean',
                'Last checked': 'Fri Sep 8 08:17:02 2023',
                'Lifetime writes': '865 GB', 'Mount count': '67',
            }, '')),
            mock.patch.object(linux_health, '_storage_identity', return_value=
                              '/dev/mmcblk0; name: USDU1; capacity: 14.7 GB'),
            mock.patch.object(linux_health, '_power_status', return_value=
                              ('ok', 'throttled=0x0')),
            mock.patch.object(linux_health, '_cpu_temperature', return_value=
                              ('ok', 48.7)),
            mock.patch.object(linux_health, '_memory_usage', return_value=
                              ('ok', 23.0, 1400000000)),
            mock.patch.object(linux_health, '_load_average', return_value=
                              ('ok', (0.24, 0.22, 0.19, 4))),
            mock.patch.object(linux_health, '_failed_units', return_value=([], '')),
            mock.patch.object(linux_health, '_kernel_messages', return_value=
                              ('Linux kernel initialized', 'journalctl', '')),
            mock.patch.object(linux_health, '_system_messages', return_value=('', '')),
        )

    def test_clean_linux_and_sd_card_report_ok(self):
        patches = self._common_patches()
        with patches[0], patches[1], patches[2], patches[3], patches[4], \
                patches[5], patches[6], patches[7], patches[8], patches[9], \
                patches[10], patches[11], patches[12], patches[13]:
            result = linux_health._collect_linux_health()

        self.assertEqual(result['status'], 'ok')
        self.assertIn('[{}]'.format(_('OK')), result['details'])
        self.assertIn('/dev/mmcblk0p2', result['details'])
        self.assertIn('USDU1', result['details'])
        self.assertIn('865 GB', result['details'])
        self.assertIn('throttled=0x0', result['details'])

    def test_storage_and_kernel_failures_report_error(self):
        patches = self._common_patches()
        with patches[0], mock.patch.object(linux_health, '_root_mount', return_value={
                'source': '/dev/mmcblk0p2', 'fstype': 'ext4', 'options': {'ro'},
        }), patches[2], patches[3], mock.patch.object(
                linux_health, '_write_probe', return_value=(False, 'read-only')), \
                mock.patch.object(linux_health, '_ext4_metadata', return_value=({
                    'Filesystem state': 'errors',
                }, '')), patches[6], mock.patch.object(
                    linux_health, '_power_status',
                    return_value=('error', 'throttled=0x1')), patches[8], \
                patches[9], patches[10], patches[11], mock.patch.object(
                    linux_health, '_kernel_messages', return_value=(
                        'Buffer I/O error on dev mmcblk0p2\nKernel panic - not syncing',
                        'journalctl', '')), patches[13]:
            result = linux_health._collect_linux_health()

        self.assertEqual(result['status'], 'error')
        self.assertIn('[{}]'.format(_('Critical')), result['details'])
        self.assertIn('Buffer I/O error', result['details'])
        self.assertIn('Kernel panic', result['details'])
        self.assertTrue(result['solution'])

    def test_missing_kernel_permissions_are_contained_as_warning(self):
        patches = self._common_patches()
        with patches[0], patches[1], patches[2], patches[3], patches[4], \
                patches[5], patches[6], patches[7], patches[8], patches[9], \
                patches[10], patches[11], mock.patch.object(
                    linux_health, '_kernel_messages',
                    return_value=('', '', 'permission denied')), patches[13]:
            result = linux_health._collect_linux_health()

        self.assertEqual(result['status'], 'warning')
        self.assertIn('permission denied', result['details'])

    def test_refresh_contains_unexpected_failure(self):
        previous_cache = dict(linux_health._cache)
        previous_refreshing = linux_health._refreshing
        self.addCleanup(setattr, linux_health, '_cache', previous_cache)
        self.addCleanup(setattr, linux_health, '_refreshing', previous_refreshing)
        linux_health._refreshing = True

        with mock.patch.object(
                linux_health, '_collect_linux_health',
                side_effect=RuntimeError('simulated failure')):
            linux_health._refresh()

        self.assertEqual(linux_health._cache['status'], 'unknown')
        self.assertIn('RuntimeError', linux_health._cache['details'])
        self.assertFalse(linux_health._refreshing)


if __name__ == '__main__':
    unittest.main()
