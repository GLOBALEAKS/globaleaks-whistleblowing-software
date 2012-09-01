# -*- coding: UTF-8
#   api
#   ***
#   :copyright: 2012 Hermes No Profit Association - GlobaLeaks Project
#   :author: Arturo Filastò <art@globaleaks.org>
#   :license: see LICENSE file
#
#   Contains all the logic for handling tip related operations.
#   This contains the specification of the API.
#   Read this if you want to have an overall view of what API calls are handled
#   by what.
from globaleaks import config
from globaleaks.rest.handlers import *
from globaleaks.submission import Submission
from cyclone.web import StaticFileHandler

tip_regexp = '\w+'
submission_id_regexp = '\w+'
module_regexp = '\w+'
id_regexp = '\w+'

spec = [
    ## Node Handler ##
    #  * /node P1
    (r'/node', nodeHandler),

    ## Submission Handlers ##
    #  * /submission/<ID>/ P2
    (r'/submission', submissionHandler,
                     dict(action='new',
                          supportedMethods=['GET']
                         )),

    #  * /submission/<ID>/status P3
    (r'/submission/(' + submission_id_regexp + ')/status',
                     submissionHandler,
                     dict(action='status',
                          supportedMethods=['GET', 'POST']
                         )),

    #  * /submission/<ID>/finalize P4
    (r'/submission/(' + submission_id_regexp + ')/finalize',
                     submissionHandler,
                     dict(action='finalize',
                          supportedMethods=['POST']
                         )),

    #  * /submission/<ID>/files P5
    (r'/submission/(' + submission_id_regexp + ')/files',
                     submissionHandler,
                     dict(action='files',
                          supportedMethods=['GET', 'POST', 'PUT', 'DELETE']
                         )),
    # https://docs.google.com/a/apps.globaleaks.org/document/d/17GXsnczhI8LgTNj438oWPRbsoz_Hs3TTSnK7NzY86S4/edit?pli=1

    ## Tip Handlers ##
    #  * /tip/<ID>/ T1
    (r'/tip/(' + tip_regexp + ')',
                     tipHandler,
                     dict(action='main',
                          supportedMethods=['GET', 'POST']
                         )),

    #  * /tip/<ID>/comment T2
    (r'/tip/(' + tip_regexp + ')/comment',
                     tipHandler,
                     dict(action='comment',
                          supportedMethods=['POST']
                         )),

    #  * /tip/<ID>/files T3
    (r'/tip/(' + tip_regexp + ')/files',
                     tipHandler,
                     dict(action='files',
                          supportedMethods=['GET', 'POST', 'PUT', 'DELETE']
                         )),

    #  * /tip/<ID>/finalize T4
    (r'/tip/(' + tip_regexp + ')/finalize',
                     tipHandler,
                     dict(action='finalize',
                          supportedMethods=['POST']
                         )),

    #  * /tip/<ID>/download T5
    (r'/tip/(' + tip_regexp + ')/download',
                     tipHandler,
                     dict(action='dowload',
                          supportedMethods=['GET']
                         )),

    #  * /tip/<ID>/pertinence T6
    (r'/tip/(' + tip_regexp + ')/pertinence',
                     tipHandler,
                     dict(action='pertinence',
                          supportedMethods=['GET']
                         )),

    ## Receiver Handlers ##
    #  * /reciever/<ID>/ R1
    (r'/receiver/(' + tip_regexp + ')',
                     receiverHandler,
                     dict(action='main',
                          supportedMethods=['GET']
                         )),

    #  * /receiver/<ID>/<MODULE TYPE> R2
    (r'/receiver/(' + tip_regexp + ')/(' + module_regexp + ')',
                     receiverHandler,
                     dict(action='module',
                          supportedMethods=['GET', 'POST', 'PUT', 'DELETE']
                         )),

    ## Admin Handlers ##
    #  * /admin/node
    (r'/admin/node', adminHandler,
                        dict(action='node',
                             supportedMethods=['GET', 'POST']
                            )),

    #  * /admin/contexts
    (r'/admin/contexts', adminHandler,
                        dict(action='context',
                             supportedMethods=['GET', 'POST', 'PUT', 'DELETE']
                            )),

    #  * /admin/groups/<ID>
    (r'/admin/groups/(' + id_regexp + ')',
                    adminHandler,
                    dict(action='groups',
                         supportedMethods=['GET', 'POST', 'PUT', 'DELETE']
                        )),

    #  * /admin/receivers/<ID>
    (r'/admin/receivers/(' + id_regexp + ')',
                    adminHandler,
                    dict(action='receivers',
                         supportedMethods=['GET', 'POST', 'PUT', 'DELETE']
                        )),

    #  * /admin/modules/<MODULE TYPE>
    (r'/admin/modules/(' + module_regexp + ')', adminHandler,
                    dict(action='module',
                         supportedMethods=['GET', 'POST']
                        )),

    ## Main Web app ##
    # * /
    (r"/(.*)", StaticFileHandler, {'path': config.glbackend.glclient_path})
    ]

