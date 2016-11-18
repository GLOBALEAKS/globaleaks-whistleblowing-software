# -*- coding: UTF-8
#
# token
#   *****
#
#   Implements a GlobaLeaks security token, to prevent resources exhaustion
#   operation by anonymous user.

from random import randint
from datetime import datetime, timedelta

import os
from globaleaks.anomaly import Alarm

from globaleaks.utils.utility import log, datetime_now, datetime_to_ISO8601
from globaleaks.rest import errors
from globaleaks.utils.tempdict import TempDict
from globaleaks.settings import GLSettings
from globaleaks.security import sha256, generateRandomKey


class TokenListClass(TempDict):
    def __init__(self, *args, **kwds):
        TempDict.__init__(self, *args, **kwds)

    def get_timeout(self):
        return GLSettings.memory_copy.submission_minimum_delay + \
               GLSettings.memory_copy.submission_maximum_ttl

    def expireCallback(self, item):
        for f in item.uploaded_files:
            # TODO delete from GLUploadFile
            try:
                os.remove(f['encrypted_path'])
            except Exception:
                pass

    def get(self, key):
        ret = TempDict.get(self, key)
        if ret is None:
            raise errors.TokenFailure("Not found")

        return ret


TokenList = TokenListClass()


class Token(object):
    MAX_USES = 30

    def __init__(self, token_kind="submission", uses=MAX_USES):
        self.id = generateRandomKey(42)
        self.kind = token_kind
        self.remaining_uses = uses
        self.creation_date = datetime.utcnow()

        # Keeps track of the file uploaded associated
        self.uploaded_files = []

        # The token challenges in their default state
        self.human_captcha = {'solved': True}
        self.proof_of_work = {'solved': True}
        self.generate_token_challenges()

        TokenList.set(self.id, self)

    def associate_file(self, fileinfo):
        self.uploaded_files.append(fileinfo)

    def __repr__(self):
        test_desc = "challenges:"
        dump_attr = ['human_captcha', 'proof_of_work']

        for a in dump_attr:
          test_desc = "%s %s=%s" % (test_desc, a, getattr(self, a))

        token_string = "<Token %s for %s [%s]>" % (self.id, self.kind, test_desc)

        return token_string

    def serialize(self):
        r = {
            'id': self.id,
            'creation_date': datetime_to_ISO8601(self.creation_date),
            'remaining_uses': self.remaining_uses,
            'type': self.kind,
            'human_captcha': False,
            'proof_of_work': False,
            'human_captcha_answer': 0,
            'proof_of_work_answer': 0
        }

        if not self.human_captcha['solved']:
            r['human_captcha'] = self.human_captcha['question']
        if not self.proof_of_work['solved']:
            r['proof_of_work'] = self.proof_of_work['question']

        return r

    def generate_token_challenges(self):
        if Alarm.stress_levels['activity'] >= 1 and GLSettings.memory_copy.enable_captcha:
            random_a = randint(0, 99)
            random_b = randint(0, 99)

            self.human_captcha = {
                'question': u"%d + %d" % (random_a, random_b),
                'answer': random_a + random_b,
                'solved': False
            }

        if GLSettings.memory_copy.enable_proof_of_work:
            self.proof_of_work = {
                'question': generateRandomKey(20),
                'solved': False
            }

    def timedelta_check(self):
        """
        timedelta_check verifies that the current time is between the start
        validity time and the end validity time.
        """
        min_delay = GLSettings.memory_copy.submission_minimum_delay
        max_ttl = GLSettings.memory_copy.submission_maximum_ttl

        now = datetime_now()
        start = (self.creation_date + timedelta(seconds=min_delay))
        if not start < now:
            log.debug("creation + validity (%d) = %s < now %s, still too early" %
                      (min_delay, start, now))
            raise errors.TokenFailure("Too early to use this token")

        end = (self.creation_date + timedelta(max_ttl))
        if now > end:
            log.debug("creation + end_validity (%d) = %s > now %s, too late" %
                      (max_ttl, start, now))
            raise errors.TokenFailure("Too late to use this token")

    def captcha_valid(self, request_answer):
        if self.human_captcha['answer'] != request_answer:
            return
        self.human_captcha['solved'] = True

    def proof_of_work_valid(self, request_answer):
        """
        :param resolved_proof_of_work: a string, that has to be an integer
        :return:
        """
        HASH_ENDS_WITH = '00'

        resolved = "%s%d" % (self.proof_of_work['question'], request_answer)
        x = sha256(bytes(resolved))
        if not x.endswith(HASH_ENDS_WITH):
            log.debug("Failed proof of work validation: expected '%s' at the end of the hash %s (seeds %s + %d)" %
                      (HASH_ENDS_WITH, x, self.proof_of_work['question'], request_answer))
            return

        log.debug("Successful proof of work validation! got '%s' at the end of the hash %s (seeds %s + %d)" %
                  (HASH_ENDS_WITH, x, self.proof_of_work['question'], request_answer))

        self.proof_of_work['solved'] = True

    def decrement(self):
        self.remaining_uses -= 1
        if self.remaining_uses < 0:
            raise errors.TokenFailure("Token is no longer valid.")

    def update(self, request):
        self.decrement()

        if not self.human_captcha['solved']:
            self.captcha_valid(request['human_captcha_answer'])

        if not self.proof_of_work['solved']:
            self.proof_of_work_valid(request['proof_of_work_answer'])

        passed = self.human_captcha['solved'] and self.proof_of_work['solved']
        if not passed:
            self.generate_token_challenges()
        return passed

    def use(self):
        try:
            self.decrement()
            self.timedelta_check()
        except errors.TokenFailure as e:
            # Unrecoverable failures so immediately delete the token.
            TokenList.delete(self.id)
            raise e

        if not self.human_captcha['solved'] or not self.proof_of_work['solved']:
            raise errors.TokenFailure("Token is not solved")

    def solve(self):
        self.human_captcha = {'solved': True}
        self.proof_of_work = {'solved': True}
