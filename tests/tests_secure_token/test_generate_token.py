# coding: utf-8
from rest_framework.test import APITestCase
from rest_framework import status
from concrete_datastore.concrete.models import (
    User,
    UserConfirmation,
    SecureConnectToken,
)
from django.test import override_settings
from datetime import timedelta


@override_settings(DEBUG=True)
class GenerateTokenTestCase(APITestCase):
    def setUp(self):
        # Create a user
        self.super_user = User.objects.create_user('super_user@netsach.org')
        self.super_user.set_password('plop')
        self.super_user.set_level('superuser', commit=True)
        self.super_user.save()
        self.super_user.superuser = True
        UserConfirmation.objects.create(
            user=self.super_user, confirmed=True
        ).save()
        url_login = '/api/v1.1/auth/login/'
        resp = self.client.post(
            url_login, {"email": "super_user@netsach.org", "password": "plop"}
        )
        self.super_user_token = resp.data['token']
        self.simple_user = User.objects.create_user('simple_user@netsach.org')
        self.simple_user.set_password('plop')
        self.simple_user.set_level('simpleuser', commit=True)
        self.simple_user.save()
        self.simple_user.superuser = True
        UserConfirmation.objects.create(user=self.simple_user, confirmed=True)
        resp = self.client.post(
            url_login, {"email": "simple_user@netsach.org", "password": "plop"}
        )
        self.simple_user_token = resp.data['token']

    def test_generate_token_success(self):
        url = '/api/v1.1/secure-connect/generate-token/'

        # POST a valid email
        url_login = '/api/v1.1/auth/login/'
        # Create an object with AUTHENTICATED user
        # Login User A and user B
        resp = self.client.post(
            url,
            {"email": "super_user@netsach.org", "password": "plop"},
            HTTP_AUTHORIZATION='Token {}'.format(self.super_user_token),
        )
        self.assertEqual(
            resp.status_code, status.HTTP_201_CREATED, msg=resp.content
        )
        secure_tokens = SecureConnectToken.objects.filter(user=self.super_user)
        self.assertEqual(secure_tokens.count(), 1)
        secure_token = secure_tokens.first()
        self.assertEqual(resp.data, {'secure-token': str(secure_token.value)})

    def test_generate_token_user_forbidden(self):
        url = '/api/v1.1/secure-connect/generate-token/'

        # POST a valid email
        resp = self.client.post(
            url,
            {"email": 'simple_user@netsach.org'},
            HTTP_AUTHORIZATION='Token {}'.format(self.simple_user_token),
        )
        self.assertEqual(
            resp.status_code, status.HTTP_403_FORBIDDEN, msg=resp.content
        )
        secure_tokens = SecureConnectToken.objects.filter(
            user=self.simple_user
        )
        self.assertEqual(secure_tokens.count(), 0)

    def test_generate_token_wrong_address(self):
        url = '/api/v1.1/secure-connect/generate-token/'

        # POST a valid email
        resp = self.client.post(
            url,
            {"email": 'user42@netsach.org'},
            HTTP_AUTHORIZATION='Token {}'.format(self.super_user_token),
        )
        self.assertEqual(
            resp.status_code, status.HTTP_400_BAD_REQUEST, msg=resp.content
        )
        self.assertEqual(
            resp.data,
            {
                "message": "Wrong email address",
                "_errors": ["WRONG_EMAIL_ADDRESS"],
            },
        )

    @override_settings(MAX_SECURE_CONNECT_TOKENS=1)
    def test_generate_token_too_many_requests(self):
        url = '/api/v1.1/secure-connect/generate-token/'

        # POST a valid email
        resp = self.client.post(
            url,
            {"email": 'super_user@netsach.org'},
            HTTP_AUTHORIZATION='Token {}'.format(self.super_user_token),
        )
        secure_tokens = SecureConnectToken.objects.filter(user=self.super_user)
        self.assertEqual(secure_tokens.count(), 1)
        resp = self.client.post(
            url,
            {"email": 'super_user@netsach.org'},
            HTTP_AUTHORIZATION='Token {}'.format(self.super_user_token),
        )
        self.assertEqual(
            resp.status_code,
            status.HTTP_429_TOO_MANY_REQUESTS,
            msg=resp.content,
        )
        secure_tokens = SecureConnectToken.objects.filter(user=self.super_user)
        self.assertEqual(secure_tokens.count(), 1)

    # Set expiry to 3 days
    @override_settings(SECURE_CONNECT_EXPIRY_TIME_SECONDS=3 * 3600 * 24)
    def test_generate_token_expire_token(self):
        url = '/api/v1.1/secure-connect/generate-token/'

        # POST a valid email
        resp = self.client.post(
            url,
            {"email": 'super_user@netsach.org'},
            HTTP_AUTHORIZATION='Token {}'.format(self.super_user_token),
        )
        secure_tokens = SecureConnectToken.objects.filter(user=self.super_user)
        self.assertEqual(secure_tokens.count(), 1)
        first_token = secure_tokens.first()
        self.assertFalse(first_token.expired)
        # Expire token
        first_token.creation_date += timedelta(-10)
        first_token.save()

        # Creation of second token
        resp = self.client.post(
            url,
            {"email": 'super_user@netsach.org'},
            HTTP_AUTHORIZATION='Token {}'.format(self.super_user_token),
        )
        self.assertEqual(
            resp.status_code, status.HTTP_201_CREATED, msg=resp.content
        )
        secure_tokens = SecureConnectToken.objects.filter(user=self.super_user)
        self.assertEqual(secure_tokens.count(), 2)
        first_token.refresh_from_db()
        self.assertTrue(first_token.expired)

    def test_generate_token_serializer_error_email(self):
        url = '/api/v1.1/secure-connect/generate-token/'

        # POST an invalid email
        resp = self.client.post(
            url,
            {"email": 'user42ànetsachcom'},
            HTTP_AUTHORIZATION='Token {}'.format(self.super_user_token),
        )
        self.assertEqual(
            resp.status_code, status.HTTP_400_BAD_REQUEST, msg=resp.content
        )
        self.assertIn('_errors', resp.data)
        self.assertEqual(resp.data['_errors'], ['INVALID_DATA'])
