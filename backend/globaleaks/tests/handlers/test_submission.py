# -*- coding: utf-8 -*-
from twisted.internet.defer import inlineCallbacks

import json

from globaleaks.rest import requests, errors
from globaleaks.tests import helpers
from globaleaks.handlers import node, submission
from globaleaks.settings import GLSetting, transact_ro
from globaleaks.security import GLSecureTemporaryFile
from globaleaks.models import InternalTip

class Test_001_SubmissionCreate(helpers.TestHandlerWithPopulatedDB):
    _handler = submission.SubmissionCreate

    @inlineCallbacks
    def test_001_post(self):
        submission_desc = dict(self.dummySubmission)
        submission_desc['finalize'] = False

        handler = self.request(submission_desc, {})
        yield handler.post()

        submission_desc = self.responses[0]

        self.responses = []

        yield self.emulate_file_upload(submission_desc['id'])

        submission_desc['finalize'] = True

        handler = self.request(submission_desc, {})
        yield handler.post()

        self.assertTrue(isinstance(self.responses, list))
        self.assertEqual(len(self.responses), 1)
        self._handler.validate_message(json.dumps(self.responses[0]), requests.internalTipDesc)

class Test_002_SubmissionInstance(helpers.TestHandlerWithPopulatedDB):
    _handler = submission.SubmissionInstance

    def test_001_get_unexistent_submission(self):
        handler = self.request({})
        self.assertFailure(handler.get("unextistent"), errors.SubmissionIdNotFound)

    @inlineCallbacks
    def test_002_get_existent_submission(self):
        submissions_ids = yield self.get_finalized_submissions_ids()

        for submission_id in submissions_ids:
            handler = self.request({})
            yield handler.get(submission_id)
            self.assertTrue(isinstance(self.responses, list))
            self._handler.validate_message(json.dumps(self.responses[0]), requests.internalTipDesc)

    @inlineCallbacks
    def test_003_put_with_finalize_false(self):
        submission_desc = dict(self.dummySubmission)
        submission_desc['finalize'] = False
        del submission_desc['id']

        status = yield submission.create_submission(submission_desc, finalize=False)

        status['finalize'] = False

        handler = self.request({}, body=json.dumps(status))
        yield handler.put(status['id'])

        self.assertEqual(self.responses[0]['receipt'], '')

    @inlineCallbacks
    def test_004_put_with_finalize_true(self):
        submission_desc = dict(self.dummySubmission)
        submission_desc['finalize'] = False
        del submission_desc['id']

        status = yield submission.create_submission(submission_desc, finalize=False)

        status['finalize'] = True

        handler = self.request({}, body=json.dumps(status))
        yield handler.put(status['id'])

        self.assertNotEqual(self.responses[0]['receipt'], '')

    def test_005_delete_unexistent_submission(self):
        handler = self.request({})
        self.assertFailure(handler.delete("unextistent"), errors.SubmissionIdNotFound)

    @inlineCallbacks
    def test_006_delete_submission_not_finalized(self):
        submission_desc = dict(self.dummySubmission)
        submission_desc['finalize'] = False
        del submission_desc['id']

        status = yield submission.create_submission(submission_desc, finalize=False)

        handler = self.request({})
        yield handler.delete(status['id'])

    @inlineCallbacks
    def test_007_delete_existent_but_finalized_submission(self):
        submissions_ids = yield self.get_finalized_submissions_ids()

        for submission_id in submissions_ids:
            handler = self.request({})
            self.assertFailure(handler.delete(submission_id), errors.SubmissionConcluded)

