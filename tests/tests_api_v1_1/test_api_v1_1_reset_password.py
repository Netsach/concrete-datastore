# coding: utf-8
import uuid
import pendulum
from datetime import timedelta
from django.conf import settings
from django.test import override_settings
from rest_framework.test import APITestCase
from rest_framework import status
from concrete_datastore.concrete.models import (
    User,
    UserConfirmation,
    Email,
    PasswordChangeToken,
)


@override_settings(DEBUG=True)
class ResetPasswordTest(APITestCase):
    def setUp(self):
        # User A
        self.user = User.objects.create_user(
            email='aaaa@netsach.org', password='userA'
        )
        self.user.save()
        UserConfirmation.objects.create(user=self.user, confirmed=True).save()
        # User B
        self.userB = User.objects.create_user(
            email='bbbb@netsach.org', password='userB'
        )
        self.userB.is_active = False
        self.userB.save()
        UserConfirmation.objects.create(user=self.userB, confirmed=True).save()

    def test_reset_password_OK(self):
        reset_password_url = '/api/v1.1/auth/reset-password/'
        change_pwd_url = '/api/v1.1/auth/change-password/'

        # Request a password reset
        response = self.client.post(
            reset_password_url, data={"email": 'aaaa@netsach.org'}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(Email.objects.count(), 1)
        self.assertEqual(PasswordChangeToken.objects.count(), 1)
        reset_token = PasswordChangeToken.objects.first()

        self.assertEqual(reset_token.user.uid, self.user.uid)
        # Confirm the password reset
        rsp = self.client.post(
            change_pwd_url,
            data={
                "email": 'aaaa@netsach.org',
                "password1": "newpassword",
                "password2": "newpassword",
                "password_change_token": reset_token.uid,
            },
        )
        self.assertEqual(rsp.status_code, status.HTTP_200_OK)
        self.assertIn('token', rsp.data)

        # Verify token deleted after usage
        self.assertEqual(PasswordChangeToken.objects.count(), 0)

        # Login with the new password
        auth_url = '/api/v1.1/auth/login/'
        resp = self.client.post(
            auth_url,
            data={
                # "username": 'johndoe@netsach.org',
                "email": 'aaaa@netsach.org',
                "password": "newpassword",
            },
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('token', resp.data)

    def test_reset_password_blocked_user(self):

        reset_password_url = '/api/v1.1/auth/reset-password/'

        # Request a password reset
        response = self.client.post(
            reset_password_url, data={"email": 'bbbb@netsach.org'}
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['message'], 'invalid data')
        self.assertIn('_errors', response.data)
        self.assertEqual(response.data['_errors'], ['INVALID_DATA'])

    def test_reset_password_fail_email(self):

        reset_password_url = '/api/v1.1/auth/reset-password/'

        # Request a password reset
        response = self.client.post(
            reset_password_url, data={"email": 'azerty@netsach.org'}
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['message'], 'invalid data')
        self.assertIn('_errors', response.data)
        self.assertEqual(response.data['_errors'], ['INVALID_DATA'])

    def test_reset_password_fail_email_token_association(self):
        reset_password_url = '/api/v1.1/auth/reset-password/'
        change_pwd_url = '/api/v1.1/auth/change-password/'

        # Request a password reset
        response = self.client.post(
            reset_password_url, data={"email": 'aaaa@netsach.org'}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(PasswordChangeToken.objects.count(), 1)
        reset_token = PasswordChangeToken.objects.first()

        self.assertEqual(reset_token.user.uid, self.user.uid)
        # Confirm the password reset
        rsp = self.client.post(
            change_pwd_url,
            data={
                "email": 'bbbb@netsach.org',
                "password1": "newpassword",
                "password2": "newpassword",
                "password_change_token": reset_token.uid,
            },
        )
        self.assertEqual(rsp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(rsp.data['message'], 'invalid token')
        self.assertIn('_errors', rsp.data)
        self.assertEqual(rsp.data['_errors'], ['INVALID_TOKEN'])

    def test_reset_password_confirmation_wrong_serializers(self):
        reset_password_url = '/api/v1.1/auth/reset-password/'
        change_pwd_url = '/api/v1.1/auth/change-password/'

        # Request a password reset
        response = self.client.post(
            reset_password_url, data={"email": 'aaaa@netsach.org'}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(PasswordChangeToken.objects.count(), 1)
        reset_token = PasswordChangeToken.objects.first()

        self.assertEqual(reset_token.user.uid, self.user.uid)
        # Confirm the password reset
        rsp = self.client.post(
            change_pwd_url,
            data={
                "email": 'bbbb@netsach.org',
                "password1": "newpassword",
                "password2": "newpassword",
            },
        )
        self.assertEqual(rsp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_reset_password_fail_wrong_email_in_confirmation(self):
        reset_password_url = '/api/v1.1/auth/reset-password/'
        change_pwd_url = '/api/v1.1/auth/change-password/'

        # Request a password reset
        response = self.client.post(
            reset_password_url, data={"email": 'aaaa@netsach.org'}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(PasswordChangeToken.objects.count(), 1)
        reset_token = PasswordChangeToken.objects.first()

        self.assertEqual(reset_token.user.uid, self.user.uid)
        # Confirm the password reset
        rsp = self.client.post(
            change_pwd_url,
            data={
                "email": 'azerty@netsach.org',
                "password1": "newpassword",
                "password2": "newpassword",
                "password_change_token": reset_token.uid,
            },
        )
        self.assertEqual(rsp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(rsp.data['message'], 'Invalid data')
        self.assertIn('_errors', rsp.data)
        self.assertEqual(rsp.data['_errors'], ['INVALID_DATA'])

    def test_reset_password_fail_wrong_token_in_confirmation(self):
        reset_password_url = '/api/v1.1/auth/reset-password/'
        change_pwd_url = '/api/v1.1/auth/change-password/'

        # Request a password reset
        response = self.client.post(
            reset_password_url, data={"email": 'aaaa@netsach.org'}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(PasswordChangeToken.objects.count(), 1)
        reset_token = PasswordChangeToken.objects.first()

        self.assertEqual(reset_token.user.uid, self.user.uid)
        # Confirm the password reset
        rsp = self.client.post(
            change_pwd_url,
            data={
                "email": 'aaaa@netsach.org',
                "password1": "newpassword",
                "password2": "newpassword",
                "password_change_token": uuid.uuid4(),
            },
        )
        self.assertEqual(rsp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(rsp.data['message'], 'invalid token')
        self.assertIn('_errors', rsp.data)
        self.assertEqual(rsp.data['_errors'], ['INVALID_TOKEN'])

    def test_reset_password_fail_mismatch_passwords(self):

        reset_password_url = '/api/v1.1/auth/reset-password/'
        change_pwd_url = '/api/v1.1/auth/change-password/'

        # Request a password reset
        response = self.client.post(
            reset_password_url, data={"email": 'aaaa@netsach.org'}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(PasswordChangeToken.objects.count(), 1)
        reset_token = PasswordChangeToken.objects.first()

        self.assertEqual(reset_token.user.uid, self.user.uid)
        # Confirm the password reset
        rsp = self.client.post(
            change_pwd_url,
            data={
                "email": 'aaaa@netsach.org',
                "password1": "newpassword",
                "password2": "newpassworddd",
                "password_change_token": reset_token.uid,
            },
        )
        self.assertEqual(rsp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('_errors', rsp.data)
        self.assertEqual(rsp.data['_errors'], ['MISMATCH_PASSWORDS'])

    def test_reset_password_fail_token_too_old(self):

        reset_password_url = '/api/v1.1/auth/reset-password/'
        change_pwd_url = '/api/v1.1/auth/change-password/'

        # Request a password reset
        response = self.client.post(
            reset_password_url, data={"email": 'aaaa@netsach.org'}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(PasswordChangeToken.objects.count(), 1)
        reset_token = PasswordChangeToken.objects.first()
        reset_token.expiry_date = pendulum.now('utc')
        reset_token.save()
        self.assertEqual(reset_token.user.uid, self.user.uid)
        # Confirm the password reset
        rsp = self.client.post(
            change_pwd_url,
            data={
                "email": 'aaaa@netsach.org',
                "password1": "newpassword",
                "password2": "newpassword",
                "password_change_token": reset_token.uid,
            },
        )
        self.assertEqual(rsp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(rsp.data['message'], 'invalid token')

    @override_settings(PASSWORD_MIN_LENGTH=9)
    def test_reset_password_fail_insecure_password(self):

        reset_password_url = '/api/v1.1/auth/reset-password/'
        change_pwd_url = '/api/v1.1/auth/change-password/'

        # Request a password reset
        response = self.client.post(
            reset_password_url, data={"email": 'aaaa@netsach.org'}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(PasswordChangeToken.objects.count(), 1)
        reset_token = PasswordChangeToken.objects.first()
        reset_token.creation_date = reset_token.creation_date + timedelta(
            0, 0, 0, 0, 0, -6
        )
        reset_token.save()
        self.assertEqual(reset_token.user.uid, self.user.uid)
        # Confirm the password reset
        rsp = self.client.post(
            change_pwd_url,
            data={
                "email": 'aaaa@netsach.org',
                "password1": "weak_pwd",
                "password2": "weak_pwd",
                "password_change_token": reset_token.uid,
            },
        )
        self.assertEqual(rsp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            rsp.data['message'],
            'The password must contain at least 9 character(s).',
        )

    def test_reset_password_check_uri(self):

        reset_password_url = '/api/v1.1/auth/reset-password/'

        # Request a password reset
        response = self.client.post(
            reset_password_url, data={"email": 'aaaa@netsach.org'}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(Email.objects.count(), 1)
        email = Email.objects.first()

        self.assertEqual(PasswordChangeToken.objects.count(), 1)
        password_change_token = PasswordChangeToken.objects.first()

        uri_reset_password = (
            'https://www.netsach.org/#/reset-password/{token}/'
            'aaaa@netsach.org/'.format(token=password_change_token.uid)
        )
        expected_email_body = settings.AUTH_CONFIRM_RESET_PASSWORD_EMAIL_BODY.format(
            link=uri_reset_password
        )
        self.assertEqual(expected_email_body, email.body)

    def test_reset_password_custom_url(self):

        reset_password_url = '/api/v1.1/auth/reset-password/'

        # Request a password reset
        response = self.client.post(
            reset_password_url,
            data={
                "email": 'aaaa@netsach.org',
                'url_format': '/my-custom-url/{token}/{email}/',
            },
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(Email.objects.count(), 1)
        email = Email.objects.first()

        self.assertEqual(PasswordChangeToken.objects.count(), 1)
        password_change_token = PasswordChangeToken.objects.first()

        uri_reset_password = (
            'https://www.netsach.org/my-custom-url/{token}/'
            'aaaa@netsach.org/'.format(token=password_change_token.uid)
        )
        expected_email_body = settings.AUTH_CONFIRM_RESET_PASSWORD_EMAIL_BODY.format(
            link=uri_reset_password
        )
        self.assertEqual(expected_email_body, email.body)

    def test_reset_password_url_wrong_format(self):

        reset_password_url = '/api/v1.1/auth/reset-password/'

        #:  wrong string format, should be '/my-custom-url/{token}/{email}/'
        response = self.client.post(
            reset_password_url,
            data={
                "email": 'aaaa@netsach.org',
                'url_format': '/my-custom-url/{token}/{user_email}/',
            },
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('_errors', response.data)
        self.assertEqual(response.data['_errors'], ['INVALID_PARAMETER'])

    def test_reset_password_url_template_injection(self):
        reset_password_url = '/api/v1.1/auth/reset-password/'

        #:  wrong string format if exactly "{token}" is not in the url_format
        response = self.client.post(
            reset_password_url,
            data={
                "email": 'aaaa@netsach.org',
                'url_format': '/my-custom-url/{token.__class__.__init__.__globals__}/{email}/',
            },
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('_errors', response.data)
        self.assertEqual(response.data['_errors'], ['INVALID_PARAMETER'])
