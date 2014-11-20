# -*- coding: UTF-8
#
#   submission
#   **********
#
#   Implements a GlobaLeaks submission, then the operations performed
#   by an HTTP client in /submission URI

from twisted.internet.defer import inlineCallbacks

from globaleaks.settings import transact, transact_ro, GLSetting, stats_counter
from globaleaks.models import *
from globaleaks import security
from globaleaks.handlers.base import BaseHandler, anomaly_check
from globaleaks.handlers.admin import db_get_context_fields
from globaleaks.handlers.authentication import transport_security_check, unauthenticated
from globaleaks.rest import requests
from globaleaks.utils.utility import log, utc_future_date, datetime_now, datetime_to_ISO8601
from globaleaks.third_party import rstr
from globaleaks.rest import errors

def wb_serialize_internaltip(internaltip):

    response = {
        'id' : internaltip.id,
        'context_id': internaltip.context_id,
        'creation_date' : datetime_to_ISO8601(internaltip.creation_date),
        'expiration_date' : datetime_to_ISO8601(internaltip.expiration_date),
        'wb_fields' : internaltip.wb_fields,
        'download_limit' : internaltip.download_limit,
        'access_limit' : internaltip.access_limit,
        'mark' : internaltip.mark,
        'pertinence' : internaltip.pertinence_counter,
        'escalation_threshold' : internaltip.escalation_threshold,
        'files' : [f.id for f in internaltip.internalfiles],
        'receivers' : [r.id for r in internaltip.receivers]
    }

    return response

@transact
def create_whistleblower_tip(store, submission_desc):
    """
    The plaintext receipt is returned only now, and then is
    stored hashed in the WBtip table
    """
    assert submission_desc is not None and submission_desc.has_key('id')

    wbtip = WhistleblowerTip()

    node = store.find(Node).one()

    return_value_receipt = unicode( rstr.xeger(node.receipt_regexp) )
    wbtip.receipt_hash = security.hash_password(return_value_receipt, node.receipt_salt)

    wbtip.access_counter = 0
    wbtip.internaltip_id = submission_desc['id']
    store.add(wbtip)

    return return_value_receipt


# Remind: has a store between argumentos because called by a @ŧransact
def import_receivers(store, submission, receiver_id_list, required=False):
    context = submission.context

    # As first we check if Context has some policies
    if not context.selectable_receiver:
        for receiver in context.receivers:
            # Skip adding receivers that don't have PGP enabled if encrypted only.
            if not GLSetting.memory_copy.allow_unencrypted and \
                    receiver.gpg_key_status != u'Enabled':
                continue
            # Add only the receiver not yet associated in Many-to-Many
            check = store.find(ReceiverInternalTip,
                ( ReceiverInternalTip.receiver_id == receiver.id,
                  ReceiverInternalTip.internaltip_id == submission.id) ).one()
            if not check:
                submission.receivers.add(receiver)

        reloaded_submission = store.find(InternalTip, InternalTip.id == submission.id).one()
        log.debug("Context [%s] has a fixed receivers corpus #%d SID = %s" %
                (reloaded_submission.context.name[GLSetting.memory_copy.default_language],
                 reloaded_submission.receivers.count(), submission.id) )
        return

    # Before has been handled the 'fixed receiver corpus',
    # Below we handle receiver personal selection

    # Clean the previous list of selected Receiver
    for prevrec in submission.receivers:
        try:
            submission.receivers.remove(prevrec)
        except Exception as excep:
            log.err("Unable to remove receiver from Tip, before new reassignment")
            raise excep

    # and now clean the received list and import the new Receiver set.
    receiver_id_list = set(receiver_id_list)

    if required and (not len(receiver_id_list)):
        log.err("Receivers required to be selected, not empty")
        raise errors.SubmissionFailFields("Needed almost one Receiver selected [1]")

    if context.maximum_selectable_receivers and \
                    len(receiver_id_list) > context.maximum_selectable_receivers:
        raise errors.InvalidInputFormat("Provided an invalid number of Receivers")

    for receiver_id in receiver_id_list:
        try:
            receiver = store.find(Receiver, Receiver.id == unicode(receiver_id)).one()
        except Exception as excep:
            log.err("Receiver requested (%s) can't be found: %s" %
                    (receiver_id, excep))
            raise errors.ReceiverIdNotFound

        if not context in receiver.contexts:
            raise errors.InvalidInputFormat("Forged receiver selection, you fuzzer! <:")

        try:
            if not GLSetting.memory_copy.allow_unencrypted and \
                    receiver.gpg_key_status != u'Enabled':
                log.err("Encrypted only submissions are supported. Cannot select [%s]" % receiver_id)
                continue
            submission.receivers.add(receiver)
        except Exception as excep:
            log.err("Receiver %s can't be assigned to the tip [%s]" % (receiver_id, excep) )
            continue

        log.debug("+receiver [%s] In tip (%s) #%d" %\
                (receiver.name, submission.id, submission.receivers.count() ) )
    
    if required and submission.receivers.count() == 0:
        log.err("Receivers required to be selected, not empty")
        raise errors.SubmissionFailFields("Needed at least one Receiver selected [2]")


# Remind: it's a store without @transaction because called by a @ŧransact
def import_files(store, submission, files, finalize):
    """
    @param submission: the Storm obj
    @param files: the list of InternalFiles UUIDs
    @return:
        Look if all the files specified in the list exist,
        Look if the context *require* almost a file, raise
            an error if missed
    """
    for file_id in files:
        try:
            ifile = store.find(InternalFile, InternalFile.id == unicode(file_id)).one()
        except Exception as excep:
            log.err("Storm error, not found %s file in import_files (%s)" %
                    (file_id, excep))
            raise errors.FileIdNotFound

        ifile.internaltip_id = submission.id
   
    if finalize and submission.context.file_required and not len(files):
        log.debug("Missing file for a submission in context %s" %
                  submission.context.name)
        raise errors.FileRequiredMissing


@transact
def create_submission(store, request, finalize, language=GLSetting.memory_copy.default_language):
    context = store.find(Context, Context.id == unicode(request['context_id'])).one()
    if not context:
        log.err("Context requested: [%s] not found!" % request['context_id'])
        raise errors.ContextIdNotFound

    submission = InternalTip()

    submission.escalation_threshold = context.escalation_threshold
    submission.access_limit = context.tip_max_access
    submission.download_limit = context.file_max_download
    submission.expiration_date = utc_future_date(seconds=context.tip_timetolive)
    submission.pertinence_counter = 0
    submission.context_id = context.id
    submission.creation_date = datetime_now()

    if finalize:
        submission.mark = InternalTip._marker[1] # Finalized
    else:
        submission.mark = InternalTip._marker[0] # Submission

    try:
        store.add(submission)
    except Exception as excep:
        log.err("Storm/SQL Error: %s (create_submission)" % excep)
        raise errors.InternalServerError("Unable to commit on DB")

    try:
        import_files(store, submission, request['files'], finalize)
    except Exception as excep:
        log.err("Submission create: files import fail: %s" % excep)
        raise excep

    try:
        wb_fields = request['wb_fields']
        fields = db_get_context_fields(store, context.id, language)
        fields_ids = [ field['id'] for field in fields]
        for f in fields:
            if f['required']:
                if f['id'] not in wb_fields:
                    raise errors.SubmissionFailFields("missing required field %s" % f['id'])
        for wbf in wb_fields:
            if wbf not in fields_ids:
                raise errors.SubmissionFailFields("provided unexpected field %s" % wbf)
        submission.wb_fields = wb_fields
    except Exception as excep:
        log.err("Submission create: fields validation fail: %s" % excep)
        raise excep

    try:
        import_receivers(store, submission, request['receivers'], required=finalize)
    except Exception as excep:
        log.err("Submission create: receivers import fail: %s" % excep)
        raise excep

    submission_dict = wb_serialize_internaltip(submission)
    return submission_dict

@transact
def update_submission(store, submission_id, request, finalize, language=GLSetting.memory_copy.default_language):

    context = store.find(Context, Context.id == unicode(request['context_id'])).one()
    if not context:
        log.err("Context requested: [%s] not found!" % request['context_id'])
        raise errors.ContextIdNotFound

    submission = store.find(InternalTip, InternalTip.id == unicode(submission_id)).one()
    if not submission:
        log.err("Invalid Submission requested %s in PUT" % submission_id)
        raise errors.SubmissionIdNotFound

    # this may happen if a submission try to update a context
    if submission.context_id != context.id:
        log.err("Can't be changed context in a submission update")
        raise errors.ContextIdNotFound("Context are immutable")

    if submission.mark != InternalTip._marker[0]:
        log.err("Submission %s do not permit update (status %s)" % (submission_id, submission.mark))
        raise errors.SubmissionConcluded

    try:
        import_files(store, submission, request['files'], finalize)
    except Exception as excep:
        log.err("Submission update: files import fail: %s" % excep)
        log.exception(excep)
        raise excep

    try:
        wb_fields = request['wb_fields']
        fields = db_get_context_fields(store, context.id, language)
        fields_ids = [ field['id'] for field in fields]
        for f in fields:
            if f['required']:
                if f['id'] not in wb_fields:
                    raise errors.SubmissionFailFields("missing required field %s" % f['id'])
        for wbf in wb_fields:
            if wbf not in fields_ids:
                raise errors.SubmissionFailFields("provided unexpected field %s" % wbf)

        submission.wb_fields = wb_fields
    except Exception as excep:
        log.err("Submission update: fields validation fail: %s" % excep)
        log.exception(excep)
        raise excep

    try:
        import_receivers(store, submission, request['receivers'], required=finalize)
    except Exception as excep:
        log.err("Submission update: receiver import fail: %s" % excep)
        log.exception(excep)
        raise excep

    if finalize:
        submission.mark = InternalTip._marker[1] # Finalized

    submission_dict = wb_serialize_internaltip(submission)
    return submission_dict


@transact_ro
def get_submission(store, submission_id):
    submission = store.find(InternalTip, InternalTip.id == unicode(submission_id)).one()

    if not submission:
        log.err("Invalid Submission requested %s in GET" % submission_id)
        raise errors.SubmissionIdNotFound

    return wb_serialize_internaltip(submission)

@transact
def delete_submission(store, submission_id):
    submission = store.find(InternalTip, InternalTip.id == unicode(submission_id)).one()

    if not submission:
        log.err("Invalid Submission requested %s in DELETE" % submission_id)
        raise errors.SubmissionIdNotFound

    if submission.mark != submission._marker[0]:
        log.err("Submission %s already concluded (status: %s)" % (submission_id, submission.mark))
        raise errors.SubmissionConcluded

    store.remove(submission)


class SubmissionCreate(BaseHandler):
    """
    This class create the submission, receiving a partial wbSubmissionDesc, and
    returning a submission_id, usable in update operation.
    """

    @transport_security_check('wb')
    @unauthenticated
    @anomaly_check('new_submission')
    @inlineCallbacks
    def post(self, *uriargs):
        """
        Request: wbSubmissionDesc
        Response: wbSubmissionDesc
        Errors: ContextIdNotFound, InvalidInputFormat, SubmissionFailFields

        This creates an empty submission for the requested context,
        and returns submissionStatus with empty fields and a Submission Unique String,
        This is the unique token used during the submission procedure.
        header session_id is used as authentication secret for the next interaction.
        expire after the time set by Admin (Context dependent setting)
        """
        request = self.validate_message(self.request.body, requests.wbSubmissionDesc)

        if request['finalize']:
            stats_counter('finalized_submission')
            finalize = True
        else:
            stats_counter('new_submission')
            finalize = False

        status = yield create_submission(request, finalize)

        if finalize:
            receipt = yield create_whistleblower_tip(status)
            status.update({'receipt': receipt})
        else:
            status.update({'receipt' : ''})

        self.set_status(201) # Created
        self.finish(status)


class SubmissionInstance(BaseHandler):
    """
    This is the interface for create, populate and complete a submission.
    Relay in the client-server update and exchange of the submissionStatus message.
    """

    @transport_security_check('wb')
    @unauthenticated
    @inlineCallbacks
    def get(self, submission_id, *uriargs):
        """
        Parameters: submission_id
        Response: wbSubmissionDesc
        Errors: SubmissionIdNotFound, InvalidInputFormat

        Get the status of the current submission.
        """
        submission = yield get_submission(submission_id)

        self.set_status(200)
        self.finish(submission)

    @transport_security_check('wb')
    @unauthenticated
    @anomaly_check('finalized_submission')
    @inlineCallbacks
    def put(self, submission_id, *uriargs):
        """
        Parameter: submission_id
        Request: wbSubmissionDesc
        Response: wbSubmissionDesc
        Errors: ContextIdNotFound, InvalidInputFormat, SubmissionFailFields, SubmissionIdNotFound, SubmissionConcluded

        PUT update the submission and finalize if requested.
        """
        request = self.validate_message(self.request.body, requests.wbSubmissionDesc)

        if request['finalize']:
            stats_counter('finalized_submission')
            finalize = True
        else:
            finalize = False

        status = yield update_submission(submission_id, request, finalize, self.request.language)

        if finalize:
            receipt = yield create_whistleblower_tip(status)
            status.update({'receipt': receipt})
        else:
            status.update({'receipt' : ''})

        self.set_status(202) # Updated
        self.finish(status)


    @transport_security_check('wb')
    @unauthenticated
    @inlineCallbacks
    def delete(self, submission_id, *uriargs):
        """
        Parameter: submission_id
        Request:
        Response: None
        Errors: SubmissionIdNotFound, SubmissionConcluded

        A whistleblower is deleting a Submission because has understand that won't really 
        be an hero. :P

        This operation is available and tested but not implemented in the GLClient
        """

        yield delete_submission(submission_id)

        self.set_status(200) # Accepted
        self.finish()

