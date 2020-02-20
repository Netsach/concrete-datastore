# coding: utf-8
import uuid
from datetime import timedelta
from django.test import override_settings
from rest_framework.test import APITestCase
from rest_framework import status
from concrete_datastore.concrete.models import (
    User,
    AuthToken,
    UserConfirmation,
    PasswordChangeToken,
    DefaultDivider,
)


class PatchAccountMeChangePasswordTesCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email='user@netsach.org')
        self.user.set_password('plop')
        self.user.save()
        confirmation = UserConfirmation.objects.create(user=self.user)
        confirmation.confirmed = True
        confirmation.save()
        self.token = AuthToken.objects.create(user=self.user)

    def test_patch_password(self):
        account_me_url = '/api/v1.1/account/me/'
        login_url = '/api/v1.1/auth/login/'
        resp = self.client.patch(
            account_me_url,
            data={'password': 'test'},
            HTTP_AUTHORIZATION='Token {}'.format(self.token),
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        #:  Check that user can log in with the new password
        resp = self.client.post(
            login_url, data={'email': 'user@netsach.org', 'password': 'test'}
        )
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)


class ResetPasswordTestCase(APITestCase):
    def setUp(self):
        # Create a user
        self.user = User.objects.create_user(email='user@netsach.org')
        self.user.set_password('plop')
        self.user.save()
        confirmation = UserConfirmation.objects.create(user=self.user)
        confirmation.confirmed = True
        confirmation.save()
        self.token = AuthToken.objects.create(user=self.user)
        self.url_reset = '/api/v1.1/auth/reset-password/'
        self.url_login = '/api/v1.1/auth/login/'
        self.url_change = '/api/v1.1/auth/change-password/'

    def test_reset_password_success(self):
        self.assertEqual(PasswordChangeToken.objects.count(), 0)
        resp = self.client.post(self.url_reset, {'email': 'user@netsach.org'})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(PasswordChangeToken.objects.count(), 1)
        pwd_change_token = PasswordChangeToken.objects.first()
        resp = self.client.post(
            self.url_change,
            {
                'email': 'user@netsach.org',
                'password1': 'test',
                'password2': 'test',
                'password_change_token': str(pwd_change_token.uid),
            },
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        #:  Check that pasword was changed by attempting a login
        resp = self.client.post(
            self.url_login, {"email": "user@netsach.org", "password": "test"}
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_reset_password_failure_wrong_token(self):
        self.assertEqual(PasswordChangeToken.objects.count(), 0)
        resp = self.client.post(self.url_reset, {'email': 'user@netsach.org'})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(PasswordChangeToken.objects.count(), 1)
        resp = self.client.post(
            self.url_change,
            {
                'email': 'user@netsach.org',
                'password1': 'test',
                'password2': 'test',
                'password_change_token': str(uuid.uuid4()),
            },
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_reset_password_failure_new_pwd_same_as_old_pwd(self):
        self.assertEqual(PasswordChangeToken.objects.count(), 0)
        resp = self.client.post(self.url_reset, {'email': 'user@netsach.org'})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(PasswordChangeToken.objects.count(), 1)
        pwd_change_token = PasswordChangeToken.objects.first()
        resp = self.client.post(
            self.url_change,
            {
                'email': 'user@netsach.org',
                'password1': 'plop',
                'password2': 'plop',
                'password_change_token': str(pwd_change_token),
            },
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_reset_password_failure_diff_pwds(self):
        self.assertEqual(PasswordChangeToken.objects.count(), 0)
        resp = self.client.post(self.url_reset, {'email': 'user@netsach.org'})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(PasswordChangeToken.objects.count(), 1)
        pwd_change_token = PasswordChangeToken.objects.first()
        resp = self.client.post(
            self.url_change,
            {
                'email': 'user@netsach.org',
                'password1': 'pwd-1',
                'password2': 'pwd-2',
                'password_change_token': str(pwd_change_token),
            },
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)


@override_settings(DEBUG=True, PASSWORD_EXPIRY_TIME=2)
class ChangePasswordTestCase(APITestCase):
    def setUp(self):
        # Create a user
        self.superuser = User.objects.create_user(email='super@netsach.org')
        self.superuser.is_superuser = True
        self.superuser.admin = True
        self.superuser.is_staff = True
        self.superuser.save()
        confirmation = UserConfirmation.objects.create(user=self.superuser)
        confirmation.confirmed = True
        confirmation.save()
        self.token_su = AuthToken.objects.create(user=self.superuser)

        self.admin = User.objects.create_user(email='admin@netsach.org')
        self.admin.is_superuser = False
        self.admin.admin = True
        self.admin.is_staff = True
        self.admin.save()
        self.token_admin = AuthToken.objects.create(user=self.admin)

        self.admin2 = User.objects.create_user(email='admin2@netsach.org')
        self.admin2.is_superuser = False
        self.admin2.admin = True
        self.admin2.is_staff = True
        self.admin2.save()

        self.staff = User.objects.create_user(email='staff@netsach.org')
        self.staff.is_superuser = False
        self.staff.admin = False
        self.staff.is_staff = True
        self.staff.save()
        self.token_staff = AuthToken.objects.create(user=self.staff)

        self.staff2 = User.objects.create_user(email='staff2@netsach.org')
        self.staff2.is_superuser = False
        self.staff2.admin = False
        self.staff2.is_staff = True
        self.staff2.save()

        self.simpleuser = User.objects.create_user(email='simple@netsach.org')
        self.simpleuser.is_superuser = False
        self.simpleuser.admin = False
        self.simpleuser.is_staff = False
        self.simpleuser.set_password('passwordInitial')
        self.simpleuser.save()
        self.token_simple = AuthToken.objects.create(user=self.simpleuser)

        self.simpleuser2 = User.objects.create_user(
            email='simple2@netsach.org'
        )
        self.simpleuser2.is_superuser = False
        self.simpleuser2.admin = False
        self.simpleuser2.is_staff = False
        self.simpleuser2.set_password('passwordInitial')
        self.simpleuser2.save()

        confirmation = UserConfirmation.objects.create(user=self.simpleuser)
        confirmation.confirmed = True
        confirmation.save()

        self.divider = DefaultDivider.objects.create()

        self.url_login = '/api/v1.1/auth/login/'
        self.url_change = '/api/v1.1/auth/change-password/'

    def test_change_expired_password(self):
        self.simpleuser.password_modification_date += timedelta(-5)
        self.simpleuser.save()
        resp = self.client.post(
            self.url_login,
            {"email": "simple@netsach.org", "password": "passwordInitial"},
        )
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn('email', resp.data)
        self.assertIn('password_change_token', resp.data)

        token = resp.data['password_change_token']

        resp = self.client.post(
            self.url_change,
            {
                'email': 'simple@netsach.org',
                'password_change_token': token,
                'password1': 'test',
                'password2': 'test',
            },
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        #:  Check that pasword was changed by attempting a login
        resp = self.client.post(
            self.url_login, {"email": "simple@netsach.org", "password": "test"}
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_change_another_user_s_password(self):
        #:  #### SUCCESS CHANGE PASSSORD ####
        #:  A manager can change a simple user's password
        #:  if they have the same divider
        self.simpleuser.defaultdividers.add(self.divider)
        self.staff.defaultdividers.add(self.divider)
        resp = self.client.post(
            self.url_change,
            {
                'email': 'simple@netsach.org',
                'password1': 'pwd_from_staff',
                'password2': 'pwd_from_staff',
            },
            HTTP_AUTHORIZATION='Token {}'.format(self.token_staff),
        )

        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        #:  Check that pasword was changed by attempting a login
        resp = self.client.post(
            self.url_login,
            {"email": "simple@netsach.org", "password": "pwd_from_staff"},
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        #:  An admin can change a simple user's password
        resp = self.client.post(
            self.url_change,
            {
                'email': 'simple@netsach.org',
                'password1': 'pwd_from_admin',
                'password2': 'pwd_from_admin',
            },
            HTTP_AUTHORIZATION='Token {}'.format(self.token_admin),
        )

        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        #:  Check that pasword was changed by attempting a login
        resp = self.client.post(
            self.url_login,
            {"email": "simple@netsach.org", "password": "pwd_from_admin"},
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        #:  A superuser can change a simple user's password
        resp = self.client.post(
            self.url_change,
            {
                'email': 'simple@netsach.org',
                'password1': 'pwd_from_su',
                'password2': 'pwd_from_su',
            },
            HTTP_AUTHORIZATION='Token {}'.format(self.token_su),
        )

        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        #:  Check that pasword was changed by attempting a login
        resp = self.client.post(
            self.url_login,
            {"email": "simple@netsach.org", "password": "pwd_from_su"},
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        #:  An admin can change a manager's password
        resp = self.client.post(
            self.url_change,
            {
                'email': 'staff@netsach.org',
                'password1': 'pwd_from_admin',
                'password2': 'pwd_from_admin',
            },
            HTTP_AUTHORIZATION='Token {}'.format(self.token_admin),
        )

        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        #:  Check that pasword was changed by attempting a login
        resp = self.client.post(
            self.url_login,
            {"email": "staff@netsach.org", "password": "pwd_from_admin"},
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        #:  A superuser can change a manager's password
        resp = self.client.post(
            self.url_change,
            {
                'email': 'staff@netsach.org',
                'password1': 'pwd_from_su',
                'password2': 'pwd_from_su',
            },
            HTTP_AUTHORIZATION='Token {}'.format(self.token_su),
        )

        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        #:  Check that pasword was changed by attempting a login
        resp = self.client.post(
            self.url_login,
            {"email": "staff@netsach.org", "password": "pwd_from_su"},
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        #:  A superuser can change an admin's password
        resp = self.client.post(
            self.url_change,
            {
                'email': 'admin@netsach.org',
                'password1': 'pwd_from_su',
                'password2': 'pwd_from_su',
            },
            HTTP_AUTHORIZATION='Token {}'.format(self.token_su),
        )

        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        #:  Check that pasword was changed by attempting a login
        resp = self.client.post(
            self.url_login,
            {"email": "admin@netsach.org", "password": "pwd_from_su"},
        )
        self.assertEqual(
            resp.status_code, status.HTTP_200_OK, msg=resp.content
        )

        #:  #### FAILURE CHANGE PASSSORD ####
        #:  A manager cannot change a simple user's password
        #:  if they do not have the same divider
        resp = self.client.post(
            self.url_change,
            {
                'email': 'simple2@netsach.org',
                'password1': 'pwd_from_staff',
                'password2': 'pwd_from_staff',
            },
            HTTP_AUTHORIZATION='Token {}'.format(self.token_staff),
        )

        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

        #:  An admin can not change a superuser's password
        resp = self.client.post(
            self.url_change,
            {
                'email': 'super@netsach.org',
                'password1': 'pwd_from_admin',
                'password2': 'pwd_from_admin',
            },
            HTTP_AUTHORIZATION='Token {}'.format(self.token_admin),
        )
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

        #:  An admin can not change an admin's password
        resp = self.client.post(
            self.url_change,
            {
                'email': 'admin2@netsach.org',
                'password1': 'pwd_from_admin',
                'password2': 'pwd_from_admin',
            },
            HTTP_AUTHORIZATION='Token {}'.format(self.token_admin),
        )
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

        #:  A manager can not change a superuser's password
        resp = self.client.post(
            self.url_change,
            {
                'email': 'super@netsach.org',
                'password1': 'pwd_from_staff',
                'password2': 'pwd_from_staff',
            },
            HTTP_AUTHORIZATION='Token {}'.format(self.token_staff),
        )
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

        #:  A manager can not change an admin's password
        resp = self.client.post(
            self.url_change,
            {
                'email': 'admin@netsach.org',
                'password1': 'pwd_from_staff',
                'password2': 'pwd_from_staff',
            },
            HTTP_AUTHORIZATION='Token {}'.format(self.token_staff),
        )
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

        #:  A manager can not change a manager's password
        resp = self.client.post(
            self.url_change,
            {
                'email': 'staff2@netsach.org',
                'password1': 'pwd_from_staff',
                'password2': 'pwd_from_staff',
            },
            HTTP_AUTHORIZATION='Token {}'.format(self.token_staff),
        )
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

        #:  A simpleuser can not change a superuser's password
        resp = self.client.post(
            self.url_change,
            {
                'email': 'super@netsach.org',
                'password1': 'pwd_from_simple',
                'password2': 'pwd_from_simple',
            },
            HTTP_AUTHORIZATION='Token {}'.format(self.token_simple),
        )
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

        #:  A simpleuser can not change an admin's password
        resp = self.client.post(
            self.url_change,
            {
                'email': 'admin@netsach.org',
                'password1': 'pwd_from_simple',
                'password2': 'pwd_from_simple',
            },
            HTTP_AUTHORIZATION='Token {}'.format(self.token_simple),
        )
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

        #:  A simpleuser can not change a manager's password
        resp = self.client.post(
            self.url_change,
            {
                'email': 'staff@netsach.org',
                'password1': 'pwd_from_simple',
                'password2': 'pwd_from_simple',
            },
            HTTP_AUTHORIZATION='Token {}'.format(self.token_simple),
        )
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

        #:  A simpleuser can not change a simpleuser's password
        resp = self.client.post(
            self.url_change,
            {
                'email': 'simple2@netsach.org',
                'password1': 'pwd_from_simple',
                'password2': 'pwd_from_simple',
            },
            HTTP_AUTHORIZATION='Token {}'.format(self.token_simple),
        )
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)
