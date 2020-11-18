# -*- coding: utf-8 -*-

# urls is used by web.py. When a GET request is received, the corresponding class is executed.

import api
import plugins

urls = [
    '/login', 'ospy.webpages.login_page',
    '/logout', 'ospy.webpages.logout_page',

    '/',  'ospy.webpages.home_page',
    '/action', 'ospy.webpages.action_page',

    '/programs', 'ospy.webpages.programs_page',
    '/program/(new|[0-9]+)', 'ospy.webpages.program_page',

    '/plugins_manage', 'ospy.webpages.plugins_manage_page',
    '/plugins_install', 'ospy.webpages.plugins_install_page',

    '/runonce', 'ospy.webpages.runonce_page',

    '/log', 'ospy.webpages.log_page',
    '/options', 'ospy.webpages.options_page',
    '/stations', 'ospy.webpages.stations_page',
    '/help', 'ospy.webpages.help_page',

    '/status.json', 'ospy.webpages.api_status_json',
    '/log.json', 'ospy.webpages.api_log_json',
    '/balance.json', 'ospy.webpages.api_balance_json',

    '/api', api.get_app(),
    '/plugins', plugins.get_app(),
    '/plugindata', 'ospy.webpages.api_plugin_data',
    '/update_status', 'ospy.webpages.api_update_status',
    '/update_footer', 'ospy.webpages.api_update_footer',

    '/download', 'ospy.webpages.download_page',
    '/upload', 'ospy.webpages.upload_page',
    '/db_unreachable', 'ospy.webpages.db_unreachable_page',
    '/uploadSSL', 'ospy.webpages.upload_page_SSL',

    '/images', 'ospy.webpages.images_page',
    '/img_edit/(new|[0-9]+)', 'ospy.webpages.image_edit_page',
    '/img_view/(new|[0-9]+)', 'ospy.webpages.image_view_page',

    '/users', 'ospy.webpages.users_page',
    '/user/(new|[0-9]+)', 'ospy.webpages.user_page',

]
