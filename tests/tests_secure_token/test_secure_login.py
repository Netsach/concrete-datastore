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
import uuid


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

    def test_secure_login_success(self):
        retrieve_url = '/api/v1.1/secure-connect/retrieve-token/'
        login_url = '/api/v1.1/secure-connect/login/'

        # POST a valid email
        resp = self.client.post(retrieve_url, {"email": 'usera@netsach.org'},)
        secure_tokens = SecureConnectToken.objects.filter(user=self.userA)
        self.assertEqual(secure_tokens.count(), 1)
        first_token = secure_tokens.first()

        resp = self.client.post(login_url, {"token": str(first_token.value)},)
        self.assertEqual(
            resp.status_code, status.HTTP_200_OK, msg=resp.content
        )
        self.assertIn('token', resp.data)
        self.assertIn('email', resp.data)
        self.assertIn('first_name', resp.data)
        self.assertIn('last_name', resp.data)
        self.assertIn('uid', resp.data)

    def test_secure_login_not_existing_token(self):
        login_url = '/api/v1.1/secure-connect/login/'

        resp = self.client.post(login_url, {"token": str(uuid.uuid4())},)
        self.assertEqual(
            resp.status_code, status.HTTP_401_UNAUTHORIZED, msg=resp.content
        )
        self.assertEqual(
            resp.data,
            {'message': 'Invalid token', "_errors": ["INVALID_TOKEN"]},
        )

    def test_secure_login_not_uid_token(self):
        login_url = '/api/v1.1/secure-connect/login/'

        resp = self.client.post(login_url, {"token": "NOT_A_TOKEN"},)
        self.assertEqual(
            resp.status_code, status.HTTP_400_BAD_REQUEST, msg=resp.content
        )
        self.assertEqual(resp.data['_errors'], ['INVALID_DATA'])

    # Set expiry to 3 days
    @override_settings(SECURE_CONNECT_EXPIRY_TIME_DAYS=3)
    def test_secure_login_expire_token(self):
        retrieve_url = '/api/v1.1/secure-connect/retrieve-token/'
        login_url = '/api/v1.1/secure-connect/login/'

        # POST a valid email
        resp = self.client.post(retrieve_url, {"email": 'usera@netsach.org'},)
        secure_tokens = SecureConnectToken.objects.filter(user=self.userA)
        self.assertEqual(secure_tokens.count(), 1)
        first_token = secure_tokens.first()
        self.assertFalse(first_token.expired)
        # Expire token
        first_token.creation_date += timedelta(-10)
        first_token.save()
        self.assertFalse(first_token.expired)
        resp = self.client.post(login_url, {"token": str(first_token.value)},)
        self.assertEqual(
            resp.status_code, status.HTTP_403_FORBIDDEN, msg=resp.content
        )
        self.assertEqual(
            resp.data,
            {"message": "Token has expired", "_errors": ["TOKEN_HAS_EXPIRED"]},
        )
        first_token.refresh_from_db()
        self.assertTrue(first_token.expired)
