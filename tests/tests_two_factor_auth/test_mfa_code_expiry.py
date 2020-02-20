# coding: utf-8
import pendulum
from rest_framework.test import APITestCase
from rest_framework import status
from django.test import override_settings
from concrete_datastore.concrete.models import (
    User,
    UserConfirmation,
    TemporaryToken,
    EmailDevice,
)


@override_settings(
    USE_TWO_FACTOR_AUTH=True,
    MFA_RULE_PER_USER=(
        'tests.tests_two_factor_auth.' 'two_factor_rules.test_mfa_rule_admin'
    ),
    TWO_FACTOR_CODE_TIMEOUT_SECONDS=120,
)
class AuthTwoFactorFailureTestCase(APITestCase):
    def setUp(self):
        # Create a user
        self.user = User.objects.create_user(
            email='johndoe@netsach.org', password='plop'
        )
        self.user.set_level('superuser')
        self.user.save()
        self.confirmation = UserConfirmation.objects.create(user=self.user)
        self.confirmation.confirmed = True
        self.confirmation.save()

    def test_basic_authentication_wrong_email_address(self):
        url = '/api/v1.1/auth/login/'
        url_two_fact = '/api/v1.1/auth/two-factor/login/'
        self.assertEqual(TemporaryToken.objects.count(), 0)
        resp = self.client.post(
            url, {"email": 'johndoe@netsach.org', "password": "plop"}
        )
        self.assertEqual(
            resp.status_code, status.HTTP_200_OK, msg=resp.content
        )
        self.assertIn('token', resp.data)
        self.assertIn('is_verified', resp.data)
        self.assertIn('email', resp.data)
        self.assertIn('first_name', resp.data)
        self.assertIn('last_name', resp.data)
        self.assertIn('uid', resp.data)
        self.assertFalse(resp.data['is_verified'])
        self.assertEqual(TemporaryToken.objects.count(), 1)
        temp_token = TemporaryToken.objects.first()
        self.assertEqual(TemporaryToken.objects.count(), 1)
        self.assertEqual(temp_token.key, resp.data['token'])

        # POST an invalid email
        resp = self.client.post(
            url_two_fact,
            {
                "email": 'invalid-email@netsach.org',
                "token": resp.data['token'],
                "verification_code": 'randoom_code',
            },
        )
        self.assertEqual(
            resp.status_code, status.HTTP_401_UNAUTHORIZED, msg=resp.content
        )

        self.assertEqual(resp.data['_errors'], ["WRONG_AUTH_CREDENTIALS"])

    def test_basic_authentication_wrong_token(self):
        url = '/api/v1.1/auth/login/'
        url_two_fact = '/api/v1.1/auth/two-factor/login/'
        self.assertEqual(TemporaryToken.objects.count(), 0)
        resp = self.client.post(
            url, {"email": 'johndoe@netsach.org', "password": "plop"}
        )
        self.assertEqual(
            resp.status_code, status.HTTP_200_OK, msg=resp.content
        )
        self.assertIn('token', resp.data)
        self.assertIn('is_verified', resp.data)
        self.assertIn('email', resp.data)
        self.assertIn('first_name', resp.data)
        self.assertIn('last_name', resp.data)
        self.assertIn('uid', resp.data)
        self.assertFalse(resp.data['is_verified'])
        self.assertEqual(TemporaryToken.objects.count(), 1)
        temp_token = TemporaryToken.objects.first()
        self.assertEqual(TemporaryToken.objects.count(), 1)
        self.assertEqual(temp_token.key, resp.data['token'])

        # POST an invalid email
        resp = self.client.post(
            url_two_fact,
            {
                "email": 'johndoe@netsach.org',
                "token": 'INVALID_TOKEN',
                "verification_code": 'randoom_code',
            },
        )
        self.assertEqual(
            resp.status_code, status.HTTP_401_UNAUTHORIZED, msg=resp.content
        )

        self.assertEqual(resp.data['_errors'], ["MFA_TEMP_TOKEN_INVALID"])

    def test_basic_authentication_temp_token_expired(self):
        """
        Test basic auth workflow
        """
        url = '/api/v1.1/auth/login/'
        url_two_fact = '/api/v1.1/auth/two-factor/login/'

        # POST a valid user/password and get a session ID (200)
        self.assertEqual(TemporaryToken.objects.count(), 0)
        resp = self.client.post(
            url, {"email": 'johndoe@netsach.org', "password": "plop"}
        )
        self.assertEqual(
            resp.status_code, status.HTTP_200_OK, msg=resp.content
        )
        self.assertIn('token', resp.data)
        self.assertIn('is_verified', resp.data)
        self.assertIn('email', resp.data)
        self.assertIn('first_name', resp.data)
        self.assertIn('last_name', resp.data)
        self.assertIn('uid', resp.data)
        self.assertFalse(resp.data['is_verified'])
        now = pendulum.now('utc')
        self.assertEqual(TemporaryToken.objects.count(), 1)
        temp_token = TemporaryToken.objects.first()
        temp_token.creation_date = now.add(minutes=-3)
        temp_token.save()
        self.assertEqual(TemporaryToken.objects.count(), 1)
        self.assertEqual(temp_token.key, resp.data['token'])

        resp = self.client.post(
            url_two_fact,
            {
                "email": 'johndoe@netsach.org',
                "token": resp.data['token'],
                "verification_code": 'randoom_code',
            },
        )
        self.assertEqual(
            resp.status_code, status.HTTP_401_UNAUTHORIZED, msg=resp.content
        )
        self.assertEqual(resp.data['_errors'], ["MFA_TEMP_TOKEN_EXPIRED"])
