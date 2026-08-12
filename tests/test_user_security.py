from types import SimpleNamespace
import unittest
from unittest import mock

from tests.test_support import TEST_DATA_DIR  # noqa: F401 - initializes isolation
from ospy import i18n  # noqa: F401 - installs gettext
from ospy import server
from ospy import twofactor
from ospy import webpages
from ospy.users import _User, category_key
from api.v1 import security as api_security
from api.v1.responses import APIError


class FakeSession(dict):
    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError as error:
            raise AttributeError(name) from error

    def __setattr__(self, name, value):
        self[name] = value


class FakeUsers:
    def __init__(self, items):
        self.items = list(items)

    def get(self, index=None):
        return list(self.items) if index is None else self.items[index]

    def find_by_name(self, name):
        return next((item for item in self.items if item.name == name), None)

    def add_users(self, user):
        self.items.append(user)


class UserSecurityTests(unittest.TestCase):
    def setUp(self):
        self.original_session = server.session
        server.session = FakeSession({
            'validated': True,
            'category': 'admin',
            'visitor': 'admin',
            'ip': '192.0.2.20',
        })

    def tearDown(self):
        server.session = self.original_session

    def test_legacy_user_defaults_to_two_factor_disabled(self):
        owner = SimpleNamespace(get=lambda: [])
        with mock.patch('ospy.users.options.load'), mock.patch('ospy.users.options.save'):
            user = _User(owner, -1)

        self.assertEqual(user.two_factor_method, twofactor.METHOD_NONE)
        self.assertEqual(user.two_factor_secret, '')
        self.assertEqual(user.two_factor_backup_codes, [])

    def test_legacy_numeric_and_current_string_roles_share_stable_keys(self):
        for role in range(4):
            self.assertEqual(category_key(role), str(role))
            self.assertEqual(category_key(str(role)), str(role))
        self.assertEqual(category_key('invalid'), '')

    def test_additional_user_has_independent_two_factor_settings(self):
        account = SimpleNamespace(
            name='operator', two_factor_method='totp',
            two_factor_secret='USERSECRET', two_factor_backup_codes=['old'])
        fake_users = FakeUsers([account])
        fake_options = SimpleNamespace(
            admin_user='admin', two_factor_method='email',
            two_factor_secret='ADMINSECRET', two_factor_backup_codes=['admin'])

        with mock.patch.object(webpages, 'users', fake_users), \
                mock.patch.object(webpages, 'options', fake_options):
            self.assertEqual(webpages._two_factor_method('operator'), 'totp')
            self.assertEqual(webpages._two_factor_secret('operator'), 'USERSECRET')
            webpages._set_two_factor_settings('operator', 'email', '', ['new'])

        self.assertEqual(account.two_factor_method, 'email')
        self.assertEqual(account.two_factor_backup_codes, ['new'])
        self.assertEqual(fake_options.two_factor_method, 'email')
        self.assertEqual(fake_options.two_factor_secret, 'ADMINSECRET')
        self.assertEqual(fake_options.two_factor_backup_codes, ['admin'])

    def test_mobile_login_enforces_additional_user_totp(self):
        secret = twofactor.generate_secret()
        account = SimpleNamespace(
            name='operator', two_factor_method='totp',
            two_factor_secret=secret, two_factor_backup_codes=[])
        fake_users = FakeUsers([account])

        with mock.patch.object(api_security, 'users', fake_users):
            api_security._verify_second_factor(
                'operator', 'user',
                {'two_factor_code': twofactor.totp_code(secret)})
            with self.assertRaises(APIError):
                api_security._verify_second_factor(
                    'operator', 'user', {'two_factor_code': '000000'})

    def test_invalid_existing_user_edit_does_not_partially_mutate_account(self):
        account = SimpleNamespace(
            index=0, name='operator', category='1', notes='original',
            password_salt='salt', password_hash='hash',
            two_factor_method='none', two_factor_secret='',
            two_factor_backup_codes=[])
        fake_users = FakeUsers([account])
        handler = object.__new__(webpages.user_page)
        handler.core_render = SimpleNamespace(user=lambda user, error: error)

        with mock.patch.object(webpages, 'users', fake_users), \
                mock.patch.object(webpages.web, 'input', return_value={
                    'action': 'save', 'name': 'changed-name', 'password': 'short',
                    'category': '2', 'notes': 'changed'}):
            result = handler.POST('0')

        self.assertEqual(result, 'upasslen')
        self.assertEqual(account.name, 'operator')
        self.assertEqual(account.category, '1')
        self.assertEqual(account.notes, 'original')
        self.assertEqual(account.password_hash, 'hash')

    def test_existing_user_keeps_password_when_field_is_blank(self):
        account = SimpleNamespace(
            index=0, name='operator', category='1', notes='original',
            password_salt='salt', password_hash='hash',
            two_factor_method='none', two_factor_secret='',
            two_factor_backup_codes=[])
        fake_users = FakeUsers([account])
        handler = object.__new__(webpages.user_page)

        with mock.patch.object(webpages, 'users', fake_users), \
                mock.patch.object(webpages.web, 'input', return_value={
                    'action': 'save', 'name': 'operator', 'password': '',
                    'category': '2', 'notes': 'updated'}), \
                mock.patch.object(webpages.logEV, 'save_events_log'), \
                mock.patch.object(webpages.web, 'seeother', side_effect=RuntimeError('redirect')):
            with self.assertRaisesRegex(RuntimeError, 'redirect'):
                handler.POST('0')

        self.assertEqual(account.password_salt, 'salt')
        self.assertEqual(account.password_hash, 'hash')
        self.assertEqual(account.category, '2')
        self.assertEqual(account.notes, 'updated')


if __name__ == '__main__':
    unittest.main()
