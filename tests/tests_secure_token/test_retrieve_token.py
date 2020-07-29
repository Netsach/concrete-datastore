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
class RetrieveTokenTestCase(APITestCase):
    def setUp(self):
        # Create a user
        self.userA = User.objects.create_user('usera@netsach.org')
        self.userA.set_password('plop')
        self.userA.save()
        UserConfirmation.objects.create(user=self.userA, confirmed=True).save()
        url = '/api/v1.1/auth/login/'
        self.client.post(
            url, {"email": "usera@netsach.org", "password": "plop"}
        )

    def test_retrieve_token_success(self):
        url = '/api/v1.1/secure-connect/retrieve-token/'

        # POST a valid email
        resp = self.client.post(url, {"email": 'usera@netsach.org'},)
        self.assertEqual(
            resp.status_code, status.HTTP_201_CREATED, msg=resp.content
        )
        self.assertDictEqual(
            resp.data, {'message': 'Token created and email sent'}
        )
        secure_tokens = SecureConnectToken.objects.filter(user=self.userA)
        self.assertEqual(secure_tokens.count(), 1)
        secure_token = secure_tokens.first()
        self.assertTrue(secure_token.mail_sent)

    def test_retrieve_token_wrong_address(self):
        url = '/api/v1.1/secure-connect/retrieve-token/'

        # POST a valid email
        resp = self.client.post(url, {"email": 'user42@netsach.org'},)
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
    def test_retrieve_token_too_many_requests(self):
        url = '/api/v1.1/secure-connect/retrieve-token/'

        # POST a valid email
        resp = self.client.post(url, {"email": 'usera@netsach.org'},)
        secure_tokens = SecureConnectToken.objects.filter(user=self.userA)
        self.assertEqual(secure_tokens.count(), 1)
        resp = self.client.post(url, {"email": 'usera@netsach.org'},)
        self.assertEqual(
            resp.status_code,
            status.HTTP_429_TOO_MANY_REQUESTS,
            msg=resp.content,
        )
        secure_tokens = SecureConnectToken.objects.filter(user=self.userA)
        self.assertEqual(secure_tokens.count(), 1)

    # Set expiry to 3 days
    @override_settings(SECURE_CONNECT_EXPIRY_TIME_DAYS=3)
    def test_retrieve_token_expire_token(self):
        url = '/api/v1.1/secure-connect/retrieve-token/'

        # POST a valid email
        resp = self.client.post(url, {"email": 'usera@netsach.org'},)
        secure_tokens = SecureConnectToken.objects.filter(user=self.userA)
        self.assertEqual(secure_tokens.count(), 1)
        first_token = secure_tokens.first()
        self.assertFalse(first_token.expired)
        # Expire token
        first_token.creation_date += timedelta(-10)
        first_token.save()

        # Creation of second token
        resp = self.client.post(url, {"email": 'usera@netsach.org'},)
        self.assertEqual(
            resp.status_code, status.HTTP_201_CREATED, msg=resp.content
        )
        secure_tokens = SecureConnectToken.objects.filter(user=self.userA)
        self.assertEqual(secure_tokens.count(), 2)
        first_token.refresh_from_db()
        self.assertTrue(first_token.expired)

    def test_retrieve_token_serializer_error_email(self):
        url = '/api/v1.1/secure-connect/retrieve-token/'

        # POST an invalid email
        resp = self.client.post(url, {"email": 'user42ànetsachcom'},)
        self.assertEqual(
            resp.status_code, status.HTTP_400_BAD_REQUEST, msg=resp.content
        )
        self.assertIn('_errors', resp.data)
        self.assertEqual(resp.data['_errors'], ['INVALID_DATA'])
