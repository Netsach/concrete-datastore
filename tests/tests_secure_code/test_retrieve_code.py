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


class RetrieveCodeTestCase(APITestCase):
    def setUp(self):
        # Create a user
        self.user = User.objects.create_user('usera@netsach.org')
        self.user.set_password('plop')
        self.user.save()
        UserConfirmation.objects.create(user=self.user, confirmed=True).save()

    @override_settings(SECURE_CONNECT_CODE_LENGTH=10)
    def test_retrieve_code_success(self):
        url = '/api/v1.1/secure-connect/retrieve-code/'

        # POST a valid email
        resp = self.client.post(url, {"email": 'usera@netsach.org'})
        self.assertEqual(
            resp.status_code, status.HTTP_201_CREATED, msg=resp.content
        )
        self.assertDictEqual(
            resp.data, {'message': 'Code created and email sent'}
        )
        secure_codes = SecureConnectCode.objects.filter(user=self.user)
        self.assertEqual(secure_codes.count(), 1)
        secure_code = secure_codes.first()
        self.assertTrue(secure_code.mail_sent)
        self.assertEqual(len(secure_code.value), 10)

    def test_retrieve_code_wrong_address(self):
        url = '/api/v1.1/secure-connect/retrieve-code/'

        # POST a valid email
        resp = self.client.post(url, {"email": 'user42@netsach.org'})
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

    @override_settings(MAX_SIMULTANEOUS_SECURE_CONNECT_CODES_PER_USER=1)
    def test_retrieve_code_too_many_requests(self):
        url = '/api/v1.1/secure-connect/retrieve-code/'

        # POST a valid email
        resp = self.client.post(url, {"email": 'usera@netsach.org'})
        secure_codes = SecureConnectCode.objects.filter(user=self.user)
        self.assertEqual(secure_codes.count(), 1)
        resp = self.client.post(url, {"email": 'usera@netsach.org'})
        self.assertEqual(
            resp.status_code,
            status.HTTP_429_TOO_MANY_REQUESTS,
            msg=resp.content,
        )
        secure_codes = SecureConnectCode.objects.filter(user=self.user)
        self.assertEqual(secure_codes.count(), 1)

    # Set expiry to 10 minutes
    @override_settings(SECURE_CONNECT_CODE_EXPIRY_TIME_SECONDS=60 * 10)
    def test_retrieve_code_expire_code(self):
        url = '/api/v1.1/secure-connect/retrieve-code/'

        # POST a valid email
        resp = self.client.post(url, {"email": 'usera@netsach.org'})
        secure_codes = SecureConnectCode.objects.filter(user=self.user)
        self.assertEqual(secure_codes.count(), 1)
        first_code = secure_codes.first()
        self.assertFalse(first_code.expired)
        # Expire code
        first_code.creation_date += timedelta(minutes=-11)
        first_code.save()

        # Creation of second code
        resp = self.client.post(url, {"email": 'usera@netsach.org'})
        self.assertEqual(
            resp.status_code, status.HTTP_201_CREATED, msg=resp.content
        )
        secure_codes = SecureConnectCode.objects.filter(user=self.user)
        self.assertEqual(secure_codes.count(), 2)
        first_code.refresh_from_db()
        self.assertTrue(first_code.expired)

    def test_retrieve_code_serializer_error_email(self):
        url = '/api/v1.1/secure-connect/retrieve-code/'

        # POST an invalid email
        resp = self.client.post(url, {"email": 'user42ànetsachcom'})
        self.assertEqual(
            resp.status_code, status.HTTP_400_BAD_REQUEST, msg=resp.content
        )
        self.assertIn('_errors', resp.data)
        self.assertEqual(resp.data['_errors'], ['INVALID_DATA'])
