# coding: utf-8
from rest_framework.test import APITestCase
from rest_framework import status
from concrete_datastore.concrete.models import (
    User,
    UserConfirmation,
    SecureConnectCode,
)
from django.test import override_settings
from datetime import timedelta
import uuid


@override_settings(DEBUG=True)
class RetrieveCodeTestCase(APITestCase):
    def setUp(self):
        # Create a user
        self.userA = User.objects.create_user('usera@netsach.org')
        self.userA.set_password('plop')
        self.userA.save()
        UserConfirmation.objects.create(user=self.userA, confirmed=True).save()

    def test_secure_login_success(self):
        retrieve_url = '/api/v1.1/secure-connect/retrieve-code/'
        login_url = '/api/v1.1/secure-connect/login-code/'

        # POST a valid email
        resp = self.client.post(retrieve_url, {"email": 'usera@netsach.org'})
        secure_codes = SecureConnectCode.objects.filter(user=self.userA)
        self.assertEqual(secure_codes.count(), 1)
        first_code = secure_codes.first()

        resp = self.client.post(
            login_url,
            {"email": "usera@netsach.org", "code": first_code.value},
        )
        self.assertEqual(
            resp.status_code, status.HTTP_200_OK, msg=resp.content
        )
        self.assertIn('token', resp.data)
        self.assertIn('email', resp.data)
        self.assertIn('first_name', resp.data)
        self.assertIn('last_name', resp.data)
        self.assertIn('uid', resp.data)

    def test_secure_login_not_existing_code(self):
        login_url = '/api/v1.1/secure-connect/login-code/'

        resp = self.client.post(
            login_url,
            {"email": 'usera@netsach.org', "code": "UNKNOWN_CODE"},
        )
        self.assertEqual(
            resp.status_code, status.HTTP_401_UNAUTHORIZED, msg=resp.content
        )
        self.assertIn('_errors', resp.data)
        self.assertEqual(
            resp.data, {'message': 'Invalid code', "_errors": ["INVALID_CODE"]}
        )

    def test_secure_login_not_existing_email(self):
        retrieve_url = '/api/v1.1/secure-connect/retrieve-code/'
        login_url = '/api/v1.1/secure-connect/login-code/'
        resp = self.client.post(retrieve_url, {"email": 'usera@netsach.org'})
        secure_codes = SecureConnectCode.objects.filter(user=self.userA)
        self.assertEqual(secure_codes.count(), 1)
        first_code = secure_codes.first()

        resp = self.client.post(
            login_url,
            {"email": 'unknown@netsach.org', "code": first_code.value},
        )
        self.assertEqual(
            resp.status_code, status.HTTP_401_UNAUTHORIZED, msg=resp.content
        )
        self.assertIn('_errors', resp.data)
        self.assertEqual(
            resp.data, {'message': 'Invalid code', "_errors": ["INVALID_CODE"]}
        )

    # Set expiry to 10 minutes
    @override_settings(SECURE_CONNECT_CODE_EXPIRY_TIME_SECONDS=60 * 10)
    def test_secure_login_expire_code(self):
        retrieve_url = '/api/v1.1/secure-connect/retrieve-code/'
        login_url = '/api/v1.1/secure-connect/login-code/'

        # POST a valid email
        resp = self.client.post(retrieve_url, {"email": 'usera@netsach.org'})
        secure_codes = SecureConnectCode.objects.filter(user=self.userA)
        self.assertEqual(secure_codes.count(), 1)
        first_code = secure_codes.first()
        self.assertFalse(first_code.expired)
        # Expire code
        first_code.creation_date += timedelta(minutes=-11)
        first_code.save()
        self.assertFalse(first_code.expired)
        resp = self.client.post(
            login_url,
            {"email": 'usera@netsach.org', "code": first_code.value},
        )
        self.assertEqual(
            resp.status_code, status.HTTP_403_FORBIDDEN, msg=resp.content
        )
        self.assertIn('_errors', resp.data)
        self.assertEqual(
            resp.data,
            {"message": "Code has expired", "_errors": ["CODE_HAS_EXPIRED"]},
        )
        first_code.refresh_from_db()
        self.assertTrue(first_code.expired)
