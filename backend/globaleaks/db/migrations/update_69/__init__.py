# -*- coding: UTF-8
from globaleaks.db.migrations.update import MigrationBase
from globaleaks.models import Model
from globaleaks.models.properties import *
from globaleaks.utils.utility import datetime_now, datetime_null
from globaleaks.models.enums import EnumUserRole

class User_v_68(Model):
    __tablename__ = 'user'

    id = Column(UnicodeText(36), primary_key=True, default=uuid4)
    tid = Column(Integer, default=1, nullable=False)
    creation_date = Column(DateTime, default=datetime_now, nullable=False)
    username = Column(UnicodeText, default='', nullable=False)
    salt = Column(UnicodeText(24), default='', nullable=False)
    hash = Column(UnicodeText(44), default='', nullable=False)
    name = Column(UnicodeText, default='', nullable=False)
    description = Column(JSON, default=dict, nullable=False)
    public_name = Column(UnicodeText, default='', nullable=False)
    role = Column(Enum(EnumUserRole), default='receiver', nullable=False)
    enabled = Column(Boolean, default=True, nullable=False)
    last_login = Column(DateTime, default=datetime_null, nullable=False)
    mail_address = Column(UnicodeText, default='', nullable=False)
    language = Column(UnicodeText(12), nullable=False)
    password_change_needed = Column(Boolean, default=True, nullable=False)
    password_change_date = Column(DateTime, default=datetime_null, nullable=False)
    crypto_prv_key = Column(UnicodeText(84), default='', nullable=False)
    crypto_pub_key = Column(UnicodeText(56), default='', nullable=False)
    crypto_rec_key = Column(UnicodeText(80), default='', nullable=False)
    crypto_bkp_key = Column(UnicodeText(84), default='', nullable=False)
    crypto_escrow_prv_key = Column(UnicodeText(84), default='', nullable=False)
    crypto_escrow_bkp1_key = Column(UnicodeText(84), default='', nullable=False)
    crypto_escrow_bkp2_key = Column(UnicodeText(84), default='', nullable=False)
    change_email_address = Column(UnicodeText, default='', nullable=False)
    change_email_token = Column(UnicodeText, unique=True)
    change_email_date = Column(DateTime, default=datetime_null, nullable=False)
    notification = Column(Boolean, default=True, nullable=False)
    forcefully_selected = Column(Boolean, default=False, nullable=False)
    can_delete_submission = Column(Boolean, default=False, nullable=False)
    can_postpone_expiration = Column(Boolean, default=True, nullable=False)
    can_grant_access_to_reports = Column(Boolean, default=False, nullable=False)
    can_transfer_access_to_reports = Column(Boolean, default=False, nullable=False)
    can_redact_information = Column(Boolean, default=False, nullable=False)
    can_mask_information = Column(Boolean, default=True, nullable=False)
    can_reopen_reports = Column(Boolean, default=True, nullable=False)
    can_edit_general_settings = Column(Boolean, default=False, nullable=False)
    readonly = Column(Boolean, default=False, nullable=False)
    two_factor_secret = Column(UnicodeText(32), default='', nullable=False)
    reminder_date = Column(DateTime, default=datetime_null, nullable=False)

    # BEGIN of PGP key fields
    pgp_key_fingerprint = Column(UnicodeText, default='', nullable=False)
    pgp_key_public = Column(UnicodeText, default='', nullable=False)
    pgp_key_expiration = Column(DateTime, default=datetime_null, nullable=False)
    # END of PGP key fields

    accepted_privacy_policy = Column(DateTime, default=datetime_null, nullable=False)
    clicked_recovery_key = Column(Boolean, default=False, nullable=False)


class MigrationScript(MigrationBase):
    def migrate_User(self):
        for old_obj in self.session_old.query(self.model_from['User']):
            new_obj = self.model_to['User']()
            for key in new_obj.__mapper__.column_attrs.keys():
                if key == 'tip_update_notification':
                    value = True
                else:
                    value = getattr(old_obj, key)
                setattr(new_obj, key, value)

            self.session_new.add(new_obj)
