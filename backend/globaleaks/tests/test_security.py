import binascii
import gnupg
import os
import scrypt

from cryptography.hazmat.primitives import hashes
from datetime import datetime

from twisted.trial import unittest
from globaleaks.tests import helpers
from globaleaks.security import generateRandomSalt, hash_password, check_password, change_password, \
    check_password_format, directory_traversal_check, GLSecureTemporaryFile, GLSecureFile, \
    crypto_backend, GLBPGP
from globaleaks.settings import GLSettings
from globaleaks.rest import errors


class TestPasswordManagement(unittest.TestCase):
    def test_pass_hash(self):
        dummy_password = "focaccina"

        dummy_salt = generateRandomSalt()

        sure_bin = scrypt.hash(dummy_password, dummy_salt)
        sure = binascii.b2a_hex(sure_bin)
        not_sure = hash_password(dummy_password, dummy_salt)
        self.assertEqual(sure, not_sure)

    def test_valid_password(self):
        dummy_password = dummy_salt_input = \
            "http://blog.transparency.org/wp-content/uploads/2010/05/A2_Whistelblower_poster.jpg"
        dummy_salt = generateRandomSalt()

        hashed_once = binascii.b2a_hex(scrypt.hash(dummy_password, dummy_salt))
        hashed_twice = binascii.b2a_hex(scrypt.hash(dummy_password, dummy_salt))
        self.assertTrue(hashed_once, hashed_twice)

        self.assertTrue(check_password(dummy_password, dummy_salt, hashed_once))

    def test_change_password(self):
        first_pass = helpers.VALID_PASSWORD1
        second_pass = helpers.VALID_PASSWORD2
        dummy_salt = generateRandomSalt()

        # as first we hash a "first_password" like has to be:
        hashed1 = binascii.b2a_hex(scrypt.hash(str(first_pass), dummy_salt))

        # now emulate the change unsing the globaleaks.security module
        hashed2 = change_password(hashed1, first_pass, second_pass, dummy_salt)

        # verify that second stored pass is the same
        self.assertEqual(
            hashed2,
            binascii.b2a_hex(scrypt.hash(str(second_pass), dummy_salt))
        )

    def test_change_password_fail_with_invalid_old_password(self):
        dummy_salt_input = "xxxxxxxx"
        first_pass = helpers.VALID_PASSWORD1
        second_pass = helpers.VALID_PASSWORD2
        dummy_salt = generateRandomSalt()

        # as first we hash a "first_password" like has to be:
        hashed1 = binascii.b2a_hex(scrypt.hash(str(first_pass), dummy_salt))

        # now emulate the change unsing the globaleaks.security module
        self.assertRaises(errors.InvalidOldPassword, change_password, hashed1, "invalid_old_pass", second_pass,
                          dummy_salt_input)

    def test_check_password_format(self):
        self.assertRaises(errors.InvalidInputFormat, check_password_format, "123abc")  # less than 8 chars
        self.assertRaises(errors.InvalidInputFormat, check_password_format, "withnonumbers")  # withnonumbers
        self.assertRaises(errors.InvalidInputFormat, check_password_format, "12345678")  # onlynumbers
        check_password_format("abcde12345")


class TestFilesystemAccess(helpers.TestGL):
    def test_directory_traversal_failure_on_relative_trusted_path_must_fail(self):
        self.assertRaises(Exception, directory_traversal_check, 'invalid/relative/trusted/path', "valid.txt")

    def test_directory_traversal_check_blocked(self):
        self.assertRaises(errors.DirectoryTraversalError, directory_traversal_check, GLSettings.static_path,
                          "/etc/passwd")

    def test_directory_traversal_check_allowed(self):
        valid_access = os.path.join(GLSettings.static_path, "valid.txt")
        directory_traversal_check(GLSettings.static_path, valid_access)


class TestGLSecureFiles(helpers.TestGL):
    def test_temporary_file(self):
        a = GLSecureTemporaryFile(GLSettings.tmp_upload_path)
        antani = "0123456789" * 10000
        a.write(antani)
        self.assertTrue(antani == a.read())
        a.close()
        self.assertFalse(os.path.exists(a.filepath))

    def test_temporary_file_write_after_read(self):
        a = GLSecureTemporaryFile(GLSettings.tmp_upload_path)
        antani = "0123456789" * 10000
        a.write(antani)
        self.assertTrue(antani == a.read())
        self.assertRaises(AssertionError, a.write, antani)
        a.close()

    def test_temporary_file_avoid_delete(self):
        a = GLSecureTemporaryFile(GLSettings.tmp_upload_path)
        a.avoid_delete()
        antani = "0123456789" * 10000
        a.write(antani)
        a.close()
        self.assertTrue(os.path.exists(a.filepath))
        b = GLSecureFile(a.filepath)
        self.assertTrue(antani == b.read())
        b.close()

    def test_temporary_file_lost_key_due_to_eventual_bug_or_reboot(self):
        a = GLSecureTemporaryFile(GLSettings.tmp_upload_path)
        a.avoid_delete()
        antani = "0123456789" * 10000
        a.write(antani)
        a.close()
        self.assertTrue(os.path.exists(a.filepath))
        os.remove(a.keypath)
        self.assertRaises(IOError, GLSecureFile, a.filepath)
        a.close()


class TestPGP(helpers.TestGL):
    secret_content = helpers.PGPKEYS['VALID_PGP_KEY1_PRV']

    def test_encrypt_message(self):
        fake_receiver_desc = {
            'pgp_key_public': helpers.PGPKEYS['VALID_PGP_KEY1_PUB'],
            'pgp_key_fingerprint': u'ECAF2235E78E71CD95365843C7B190543CAA7585',
            'username': u'fake@username.net',
        }

        pgpobj = GLBPGP()
        pgpobj.load_key(helpers.PGPKEYS['VALID_PGP_KEY1_PRV'])

        encrypted_body = pgpobj.encrypt_message(fake_receiver_desc['pgp_key_fingerprint'],
                                                self.secret_content)

        self.assertEqual(str(pgpobj.gnupg.decrypt(encrypted_body)), self.secret_content)

        pgpobj.destroy_environment()

    def test_encrypt_file(self):
        file_src = os.path.join(os.getcwd(), 'test_plaintext_file.txt')
        file_dst = os.path.join(os.getcwd(), 'test_encrypted_file.txt')

        fake_receiver_desc = {
            'pgp_key_public': helpers.PGPKEYS['VALID_PGP_KEY1_PRV'],
            'pgp_key_fingerprint': u'ECAF2235E78E71CD95365843C7B190543CAA7585',
            'username': u'fake@username.net',
        }

        # these are the same lines used in delivery_sched.py
        pgpobj = GLBPGP()
        pgpobj.load_key(helpers.PGPKEYS['VALID_PGP_KEY1_PRV'])

        with open(file_src, 'w+') as f:
            f.write(self.secret_content)
            f.seek(0)

            encrypted_object, length = pgpobj.encrypt_file(fake_receiver_desc['pgp_key_fingerprint'],
                                                           f,
                                                           file_dst)

        with open(file_dst, 'r') as f:
            self.assertEqual(str(pgpobj.gnupg.decrypt_file(f)), self.secret_content)

        pgpobj.destroy_environment()

    def test_read_expirations(self):
        pgpobj = GLBPGP()

        self.assertEqual(pgpobj.load_key(helpers.PGPKEYS['VALID_PGP_KEY1_PRV'])['expiration'],
                         datetime.utcfromtimestamp(0))

        self.assertEqual(pgpobj.load_key(helpers.PGPKEYS['EXPIRED_PGP_KEY_PUB'])['expiration'],
                         datetime.utcfromtimestamp(1391012793))

        pgpobj.destroy_environment()
