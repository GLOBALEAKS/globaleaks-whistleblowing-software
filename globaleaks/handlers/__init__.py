# -*- encoding: utf-8 -*-
#
# :authors: Arturo Filastò
# :licence: see LICENSE

"""
In here you will find all the handlers that are tasked with handling the
requests specified in the API.

From these handlers we will be instantiating models objects that will take care
of our business logic and the generation of the output to be sent to GLClient.

In here we are also tasked with doing the validation of the user supplied
input. This must be done before instantiating any models object.
Validation of input may be done with the functions inside of
globaleaks.messages.

See base.BaseHandler for details on the handlers.
"""
from . import base, node, admin, submission, tip, receiver, files
__all__ = ['base', 'node', 'admin', 'submission', 'tip', 'receiver', 'files']
