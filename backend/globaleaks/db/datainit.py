# -*- coding: UTF-8
# GLBackend Database
#   ******************
from __future__ import with_statement

import json

import re
import os

from globaleaks import models
from globaleaks.rest import errors, requests
from globaleaks.settings import transact, transact_ro, GLSettings
from globaleaks.security import get_salt, hash_password
from globaleaks.third_party import rstr


def load_appdata():
    """
    Setup application data evaluating the presence of the following paths:
        - production data path: /usr/share/globaleaks/glclient/data/
        - development data paths: ../client/build/data/
                                  ../client/app/data/
    """
    fields_l10n = ["/usr/share/globaleaks/glclient/data/appdata_l10n.json",
                   "../../../client/build/data/appdata_l10n.json",
                   "../../../client/app/data/appdata_l10n.json"]

    appdata_dict = None

    this_directory = os.path.dirname(__file__)

    for fl10n in fields_l10n:
        fl10n_file = os.path.join(this_directory, fl10n)

        if os.path.exists(fl10n_file):
            with file(fl10n_file, 'r') as f:
                json_string = f.read()
                appdata_dict = json.loads(json_string)
                return appdata_dict

    if not appdata_dict:
        # on this condition appdata is set to empty
        return dict({'version': 1, 'fields': []})

    return appdata_dict


@transact
def init_appdata(store, result, appdata_dict):
    # Drop old appdata
    store.find(models.ApplicationData).remove()

    # Initialize the default data table evry time with
    # fresh data and fresh translations
    appdata = models.ApplicationData()
    appdata.fields = appdata_dict['fields']
    appdata.version = appdata_dict['version']
    store.add(appdata)


@transact
def init_db(store, result, node_dict, appdata_dict):
    """
    """
    node = models.Node(node_dict)
    node.languages_enabled = GLSettings.defaults.languages_enabled
    node.receipt_salt = get_salt(rstr.xeger('[A-Za-z0-9]{56}'))
    node.wizard_done = GLSettings.skip_wizard

    for k in appdata_dict['node']:
        setattr(node, k, appdata_dict['node'][k])

    store.add(node)

    admin_salt = get_salt(rstr.xeger('[A-Za-z0-9]{56}'))
    admin_password = hash_password(u"globaleaks", admin_salt)

    admin_dict = {
        'username': u'admin',
        'password': admin_password,
        'salt': admin_salt,
        'role': u'admin',
        'state': u'enabled',
        'mail_address': u'',
        'language': u"en",
        'timezone': 0,
        'password_change_needed': False,
    }

    admin = models.User(admin_dict)
    store.add(admin)

    notification = models.Notification()
    for k in appdata_dict['templates']:
        setattr(notification, k, appdata_dict['templates'][k])

    store.add(notification)


def db_update_memory_variables(store):
    """
    to get fast checks, import (same) of the Node variable in GLSettings,
    this function is called every time that Node is updated.
    """
    try:
        node = store.find(models.Node).one()

        GLSettings.memory_copy.maximum_filesize = node.maximum_filesize
        GLSettings.memory_copy.maximum_namesize = node.maximum_namesize
        GLSettings.memory_copy.maximum_textsize = node.maximum_textsize

        GLSettings.memory_copy.tor2web_admin = node.tor2web_admin
        GLSettings.memory_copy.tor2web_submission = node.tor2web_submission
        GLSettings.memory_copy.tor2web_receiver = node.tor2web_receiver
        GLSettings.memory_copy.tor2web_unauth = node.tor2web_unauth

        GLSettings.memory_copy.submission_minimum_delay = node.submission_minimum_delay
        GLSettings.memory_copy.submission_maximum_ttl =  node.submission_maximum_ttl

        GLSettings.memory_copy.allow_unencrypted = node.allow_unencrypted
        GLSettings.memory_copy.allow_iframes_inclusion = node.allow_iframes_inclusion

        GLSettings.memory_copy.exception_email = node.exception_email
        GLSettings.memory_copy.default_language = node.default_language
        GLSettings.memory_copy.default_timezone = node.default_timezone
        GLSettings.memory_copy.languages_enabled  = node.languages_enabled

        # Email settings are copyed because they are used when an exception raises
        # and we can't go to check in the DB, because that's shall be exception source
        notif = store.find(models.Notification).one()

        GLSettings.memory_copy.notif_server = notif.server
        GLSettings.memory_copy.notif_port = notif.port
        GLSettings.memory_copy.notif_password = notif.password
        GLSettings.memory_copy.notif_username = notif.username
        GLSettings.memory_copy.notif_security = notif.security

        GLSettings.memory_copy.notification_threshold_per_hour = notif.notification_threshold_per_hour
        GLSettings.memory_copy.notification_suspension_time = notif.notification_suspension_time

        if GLSettings.developer_name:
            GLSettings.memory_copy.notif_source_name = GLSettings.developer_name
        else:
            GLSettings.memory_copy.notif_source_name = notif.source_name

        GLSettings.memory_copy.notif_source_name = notif.source_name
        GLSettings.memory_copy.notif_source_email = notif.source_email
        GLSettings.memory_copy.notif_uses_tor = notif.torify

        if GLSettings.disable_mail_notification:
            GLSettings.memory_copy.disable_receiver_notification_emails = True
            GLSettings.memory_copy.disable_admin_notification_emails = True
        else:
            GLSettings.memory_copy.disable_receiver_notification_emails = notif.disable_receivers_notification_emails
            GLSettings.memory_copy.disable_admin_notification_emails = notif.disable_admin_notification_emails

    except Exception as e:
        raise errors.InvalidInputFormat("Cannot import memory variables: %s" % e)


@transact_ro
def import_memory_variables(*args):
    return db_update_memory_variables(*args)


@transact
def apply_cli_options(store):
    """
    Remind: GLSettings.unchecked_tor_input contain data that are not
    checked until this function!
    """

    node = store.find(models.Node).one()

    verb = "Hardwriting"
    accepted = {}
    if 'hostname_tor_content' in GLSettings.unchecked_tor_input:
        composed_hs_url = 'http://%s' % GLSettings.unchecked_tor_input['hostname_tor_content']
        hs = GLSettings.unchecked_tor_input['hostname_tor_content'].split('.onion')[0]
        composed_t2w_url = 'https://%s.tor2web.org' % hs

        if not (re.match(requests.hidden_service_regexp, composed_hs_url) or
                    re.match(requests.https_url_regexp, composed_t2w_url)):
            print "[!!] Invalid content found in the 'hostname' file specified (%s): Ignored" % \
                  GLSettings.unchecked_tor_input['hostname_tor_content']
        else:
            accepted.update({'hidden_service': unicode(composed_hs_url)})
            print "[+] %s hidden service in the DB: %s" % (verb, composed_hs_url)

            if node.public_site:
                print "[!!] Public Website (%s) is not automatically overwritten by (%s)" % \
                      (node.public_site, composed_t2w_url)
            else:
                accepted.update({'public_site': unicode(composed_t2w_url)})
                print "[+] %s public site in the DB: %s" % (verb, composed_t2w_url)

            verb = "Overwriting"

    if GLSettings.cmdline_options.public_website:
        if not re.match(requests.https_url_regexp, GLSettings.cmdline_options.public_website):
            print "[!!] Invalid public site: %s: Ignored" % GLSettings.cmdline_options.public_website
        else:
            print "[+] %s public site in the DB: %s" % (verb, GLSettings.cmdline_options.public_website)
            accepted.update({'public_site': unicode(GLSettings.cmdline_options.public_website)})

    if GLSettings.cmdline_options.hidden_service:
        if not re.match(requests.hidden_service_regexp, GLSettings.cmdline_options.hidden_service):
            print "[!!] Invalid hidden service: %s: Ignored" % GLSettings.cmdline_options.hidden_service
        else:
            print "[+] %s hidden service in the DB: %s" % (verb, GLSettings.cmdline_options.hidden_service)
            accepted.update({'hidden_service': unicode(GLSettings.cmdline_options.hidden_service)})

    if accepted:
        node = store.find(models.Node).one()
        for k, v, in accepted.iteritems():
            setattr(node, k, v)

    # return configured URL for the log/console output
    node = store.find(models.Node).one()
    if node.hidden_service or node.public_site:
        return [node.hidden_service, node.public_site]
    else:
        return None
