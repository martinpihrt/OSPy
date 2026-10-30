import hashlib
import os
import tempfile
import unittest

from tests.test_support import TEST_DATA_DIR  # noqa: F401 - initializes isolation
from ospy import i18n  # noqa: F401 - installs gettext
from ospy import usagestats


class HardwareIdentifierTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.tempdir.cleanup()

    def _write(self, name, value):
        path = os.path.join(self.tempdir.name, name)
        with open(path, 'wb') as output:
            output.write(value)
        return path

    @staticmethod
    def _expected(serial):
        return hashlib.sha256(
            ('ospy-hardware-v1:' + serial).encode('ascii')
        ).hexdigest()

    def test_device_tree_serial_is_hashed_without_being_returned(self):
        serial = '100000001234abcd'
        serial_path = self._write('serial-number', serial.encode('ascii') + b'\0')
        missing_cpuinfo = os.path.join(self.tempdir.name, 'missing-cpuinfo')

        result = usagestats.hardware_identifier([serial_path], missing_cpuinfo)

        self.assertEqual(result, self._expected(serial))
        self.assertNotIn(serial, result)

    def test_cpuinfo_serial_is_used_as_fallback(self):
        cpuinfo = self._write(
            'cpuinfo',
            b'Hardware\t: BCM2835\nSerial\t\t: 00000000ABCDEF12\n',
        )

        result = usagestats.hardware_identifier(
            [os.path.join(self.tempdir.name, 'missing-serial')],
            cpuinfo,
        )

        self.assertEqual(result, self._expected('00000000abcdef12'))

    def test_untrusted_or_missing_values_do_not_create_an_identifier(self):
        invalid_serial = self._write('serial-number', b'0000000000000000\0')
        invalid_cpuinfo = self._write('cpuinfo', b'Serial: not-a-serial\n')

        result = usagestats.hardware_identifier(
            [invalid_serial],
            invalid_cpuinfo,
        )

        self.assertEqual(result, '')

    def test_reporting_flag_only_appends_available_identifier(self):
        info = []
        expected = 'a' * 64
        original = usagestats.hardware_identifier
        try:
            usagestats.hardware_identifier = lambda: expected
            usagestats.HARDWARE_IDENTITY(None, info)
        finally:
            usagestats.hardware_identifier = original

        self.assertEqual(info, [('hardware', expected)])


if __name__ == '__main__':
    unittest.main()
