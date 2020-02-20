# coding: utf-8
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
        'tests.tests_two_factor_auth.'
        'two_factor_rules.test_mfa_rule_admin'
    ),
    TWO_FACTOR_CODE_TIMEOUT_SECONDS=120
)
class AuthTwoFactorMinimumAdminTestCase(APITestCase):
    def setUp(self):
        # Create a user
        self.user = User.objects.create_user(
            email='johndoe@netsach.org', password='plop'
        )
        self.user.save()
        self.confirmation = UserConfirmation.objects.create(user=self.user)
        self.confirmation.confirmed = True
        self.confirmation.save()

    def test_basic_authentication_superuser(self):
        """
        Test basic auth workflow
        """
        url = '/api/v1.1/auth/login/'
        url_two_fact = '/api/v1.1/auth/two-factor/login/'
        url_that_require_auth = '/api/v1.1/group/'
        self.user.set_level('superuser')
        self.user.save()

        # POST a valid user/password and get a session ID (200)
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
        email_device = EmailDevice.objects.filter(user=self.user).first()
        # Regenerate a code because we don't have the email sent
        code = email_device.generate_challenge()
        temp_token = TemporaryToken.objects.first()
        self.assertEqual(TemporaryToken.objects.count(), 1)
        self.assertEqual(temp_token.key, resp.data['token'])

        resp = self.client.post(
            url_two_fact,
            {
                "email": 'johndoe@netsach.org',
                "token": resp.data['token'],
                "verification_code": code,
            },
        )
        self.assertEqual(
            resp.status_code, status.HTTP_200_OK, msg=resp.content
        )
        token = resp.data['token']

        # Use without token to access the url_that_required_auth (401)
        resp = self.client.post(url_that_require_auth)
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

        # Use with token to access the url_that_required_auth (200)
        resp = self.client.get(
            url_that_require_auth, HTTP_AUTHORIZATION='Token {}'.format(token)
        )

        self.assertEqual(
            resp.status_code, status.HTTP_200_OK, msg=resp.content
        )

    def test_basic_authentication_admin(self):
        """
        Test basic auth workflow
        """
        url = '/api/v1.1/auth/login/'
        url_two_fact = '/api/v1.1/auth/two-factor/login/'
        url_that_require_auth = '/api/v1.1/group/'
        self.user.set_level('admin')
        self.user.save()

        # POST a valid user/password and get a session ID (200)
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
        email_device = EmailDevice.objects.filter(user=self.user).first()
        # Regenerate a code because we don't have the email sent
        code = email_device.generate_challenge()
        temp_token = TemporaryToken.objects.first()
        self.assertEqual(TemporaryToken.objects.count(), 1)
        self.assertEqual(temp_token.key, resp.data['token'])

        resp = self.client.post(
            url_two_fact,
            {
                "email": 'johndoe@netsach.org',
                "token": resp.data['token'],
                "verification_code": code,
            },
        )
        self.assertEqual(
            resp.status_code, status.HTTP_200_OK, msg=resp.content
        )
        token = resp.data['token']

        # Use without token to access the url_that_required_auth (401)
        resp = self.client.post(url_that_require_auth)
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

        # Use with token to access the url_that_required_auth (200)
        resp = self.client.get(
            url_that_require_auth, HTTP_AUTHORIZATION='Token {}'.format(token)
        )

        self.assertEqual(
            resp.status_code, status.HTTP_200_OK, msg=resp.content
        )

    def test_basic_authentication_wrong_code_admin(self):
        """
        Test basic auth workflow
        """
        url = '/api/v1.1/auth/login/'
        url_two_fact = '/api/v1.1/auth/two-factor/login/'
        self.user.set_level('admin')
        self.user.save()

        # POST a valid user/password and get a session ID (200)
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
        # Regenerate a code because we don't have the email sent
        temp_token = TemporaryToken.objects.first()
        self.assertEqual(TemporaryToken.objects.count(), 1)
        self.assertEqual(temp_token.key, resp.data['token'])

        resp = self.client.post(
            url_two_fact,
            {
                "email": 'johndoe@netsach.org',
                "token": resp.data['token'],
                "verification_code": 'wrong-code',
            },
        )
        self.assertEqual(
            resp.status_code, status.HTTP_401_UNAUTHORIZED, msg=resp.content
        )

    def test_basic_authentication_manager(self):
        """
        Test basic auth workflow
        """
        url = '/api/v1.1/auth/login/'
        url_that_require_auth = '/api/v1.1/group/'
        self.user.set_level('manager')
        self.user.save()

        # POST a valid user/password and get a session ID (200)
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
        self.assertTrue(resp.data['is_verified'])
        self.assertEqual(TemporaryToken.objects.count(), 0)

        token = resp.data['token']

        # Use without token to access the url_that_required_auth (401)
        resp = self.client.post(url_that_require_auth)
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

        # Use with token to access the url_that_required_auth (200)
        resp = self.client.get(
            url_that_require_auth, HTTP_AUTHORIZATION='Token {}'.format(token)
        )

        self.assertEqual(
            resp.status_code, status.HTTP_200_OK, msg=resp.content
        )

    def test_basic_authentication_simpleuser(self):
        """
        Test basic auth workflow
        """
        url = '/api/v1.1/auth/login/'
        url_that_require_auth = '/api/v1.1/group/'
        self.user.set_level('simpleuser')
        self.user.save()

        # POST a valid user/password and get a session ID (200)
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
        self.assertTrue(resp.data['is_verified'])
        self.assertEqual(TemporaryToken.objects.count(), 0)

        token = resp.data['token']

        # Use without token to access the url_that_required_auth (401)
        resp = self.client.post(url_that_require_auth)
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

        # Use with token to access the url_that_required_auth (200)
        resp = self.client.get(
            url_that_require_auth, HTTP_AUTHORIZATION='Token {}'.format(token)
        )

        self.assertEqual(
            resp.status_code, status.HTTP_200_OK, msg=resp.content
        )
