# -*- encoding: utf-8 -*-
from __future__ import unicode_literals

from twisted.internet.defer import inlineCallbacks, returnValue

# override GLSetting
from globaleaks.settings import GLSetting, transact_ro
from globaleaks.tests import helpers
from globaleaks.jobs import delivery_sched
from globaleaks.handlers import authentication, wbtip
from globaleaks.handlers.admin import create_receiver
from globaleaks.rest import errors
from globaleaks.models import InternalTip
from globaleaks.utils.token import Token
from globaleaks.handlers.admin import get_context_steps
from globaleaks.handlers.submission import create_whistleblower_tip, \
    SubmissionCreate, SubmissionInstance

# and here, our protagonist character:
from globaleaks.handlers.submission import create_submission

@transact_ro
def collect_ifile_as_wb_without_wbtip(store, internaltip_id):
    file_list = []
    itip = store.find(InternalTip, InternalTip.id == internaltip_id).one()

    for internalfile in itip.internalfiles:
        file_list.append(wbtip.wb_serialize_file(internalfile))
    return file_list

class TestSubmission(helpers.TestGLWithPopulatedDB):
    encryption_scenario = 'ALL_PLAINTEXT'

    @inlineCallbacks
    def create_submission(self, request):
        token = Token('submission', request['context_id'])
        output = yield create_submission(token.token_id, request, True, 'en')
        returnValue(output)

    @inlineCallbacks
    def create_submission_with_files(self, request):
        token = Token('submission', request['context_id'])
        yield self.emulate_file_upload(token, 3)
        output = yield create_submission(token.token_id, request, False, 'en')
        returnValue(output)

    @inlineCallbacks
    def test_create_submission_valid_submission(self):
        self.submission_desc = yield self.get_dummy_submission(self.dummyContext['id'])
        self.submission_desc = yield self.create_submission(self.submission_desc)

    @inlineCallbacks
    def test_create_submission_with_wrong_receiver(self):
        disassociated_receiver = yield create_receiver(self.get_dummy_receiver('dumb'), 'en')
        self.submission_desc = yield self.get_dummy_submission(self.dummyContext['id'])
        self.submission_desc['receivers'].append(disassociated_receiver['id'])
        yield self.assertFailure(self.create_submission(self.submission_desc),
                                 errors.InvalidInputFormat)

    @inlineCallbacks
    def test_create_submission_attach_files_finalize_and_access_wbtip(self):
        self.submission_desc = yield self.get_dummy_submission(self.dummyContext['id'])
        self.submission_desc = yield self.create_submission_with_files(self.submission_desc)

        wb_access_id, _, _ = yield authentication.login_wb(self.submission_desc['receipt'])

        # remind: return a tuple (serzialized_itip, wb_itip)
        wb_tip = yield wbtip.get_tip(wb_access_id, 'en')

        self.assertTrue('answers' in wb_tip)

    @inlineCallbacks
    def test_create_receiverfiles_allow_unencrypted_true_no_keys_loaded(self):
        yield self.test_create_submission_attach_files_finalize_and_access_wbtip()

        yield delivery_sched.DeliverySchedule().operation()

        self.fil = yield delivery_sched.get_files_by_itip(self.submission_desc['id'])
        self.assertTrue(isinstance(self.fil, list))
        self.assertEqual(len(self.fil), 3)

        self.rfi = yield delivery_sched.get_receiverfile_by_itip(self.submission_desc['id'])
        self.assertTrue(isinstance(self.rfi, list))
        self.assertEqual(len(self.rfi), 6)

        for i in range(0, 6):
            self.assertTrue(self.rfi[i]['status'] in [u'reference', u'encrypted'])

        self.wbfls = yield collect_ifile_as_wb_without_wbtip(self.submission_desc['id'])
        self.assertEqual(len(self.wbfls), 3)

    @inlineCallbacks
    def test_submission_with_receiver_selection_allow_unencrypted_true_no_keys_loaded(self):
        self.submission_desc = yield self.get_dummy_submission(self.dummyContext['id'])
        self.submission_desc = yield self.create_submission(self.submission_desc)

    @inlineCallbacks
    def test_submission_with_receiver_selection_allow_unencrypted_false_no_keys_loaded(self):
        GLSetting.memory_copy.allow_unencrypted = False

        # Create a new request with selected three of the four receivers
        submission_request = yield self.get_dummy_submission(self.dummyContext['id'])

        yield self.assertFailure(self.create_submission(submission_request),
                                 errors.SubmissionValidationFailure)

    @inlineCallbacks
    def test_update_submission(self):
        self.submission_desc = yield self.get_dummy_submission(self.dummyContext['id'])

        self.submission_desc['answers'] = yield self.fill_random_answers(self.dummyContext['id'])
        self.submission_desc = yield self.create_submission(self.submission_desc)

        wb_access_id, _, _ = yield authentication.login_wb(self.submission_desc['receipt'])

        wb_tip = yield wbtip.get_tip(wb_access_id, 'en')

        self.assertTrue('answers' in wb_tip)


class Test_SubmissionCreate(helpers.TestHandlerWithPopulatedDB):
    _handler = SubmissionCreate

    @inlineCallbacks
    def test_post(self):
        handler = self.request(
            {
              'context_id': self.dummyContext['id'],
              'receivers': [],
              'answers': {},
              'human_captcha_answer': 0,
              'graph_captcha_answer': '',
              'proof_of_work': 0,
            }
        )
        yield handler.post()


class Test_SubmissionInstance(helpers.TestHandlerWithPopulatedDB):
    _handler = SubmissionInstance

    @inlineCallbacks
    def test_put(self):
        self.submission_desc = yield self.get_dummy_submission(self.dummyContext['id'])
        token = Token('submission', self.dummyContext['id'])

        handler = self.request(self.submission_desc)
        yield handler.put(token.token_id)
