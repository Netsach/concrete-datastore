# coding: utf-8
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import authenticate, get_user_model
from django.test import Client
from concrete_datastore.concrete.models import User, UserConfirmation
from django.test import override_settings
from unittest.mock import patch
from datetime import date, timedelta


@override_settings(DEBUG=True)
class AuthTestCase(APITestCase):
    def setUp(self):
        # Create a user
        self.user = User.objects.create_user(
            email='johndoe@netsach.org',
            password='plop',
            # 'John',
            # 'Doe',
        )
        self.confirmation = UserConfirmation.objects.create(user=self.user)
        self.confirmation.confirmed = True
        self.confirmation.save()

        # Create a blocked user
        self.user2 = User.objects.create_user(
            email='janedoe@netsach.org', password='plop'
        )
        self.user2.save()
        self.user2.level = 'blocked'

        # Create an unconfirmed user
        self.user3 = User.objects.create_user(
            email='juliadoe@netsach.org', password='plop'
        )
        self.user3.save()

    def test_authenticate_user_cant_authenticate(self):
        self.user.is_staff = True
        self.user.save()
        auth = authenticate(
            username='johndoe@netsach.org', password='plop', from_api=False
        )
        self.assertIs(auth, None)

    def test_authenticate_user_is_superuser(self):
        self.user.is_superuser = True
        self.user.save()
        auth = authenticate(
            username='johndoe@netsach.org', password='plop', from_api=False
        )
        self.assertIsNot(auth, None)

    def test_authenticate_user_can_authenticate(self):
        auth = authenticate(
            username='johndoe@netsach.org', password='plop', from_api=True
        )
        self.assertIsNot(auth, None)

    def test_basic_authentication(self):
        """
        Test basic auth workflow
        """
        url = '/api/v1.1/auth/login/'
        url_that_require_auth = '/api/v1.1/project/'

        # Ensure that a unauthenticated user cannot access the view (401)
        resp = self.client.post(url_that_require_auth)
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

        # POST a valid user/password and get a session ID (200)
        resp = self.client.post(
            url, {"email": 'johndoe@netsach.org', "password": "plop",},
        )
        self.assertEqual(
            resp.status_code, status.HTTP_200_OK, msg=resp.content
        )
        self.assertIn('token', resp.data)
        self.assertIn('email', resp.data)
        self.assertIn('first_name', resp.data)
        self.assertIn('last_name', resp.data)
        self.assertIn('uid', resp.data)
        self.assertIn('groups', resp.data)

        resp = self.client.post(
            url, {"email": 'JOHNDOE@netsach.org', "password": "plop",},
        )

        # print(resp.status_code)
        self.assertEqual(
            resp.status_code, status.HTTP_200_OK, msg=resp.content
        )

        resp = self.client.post(
            url, {"email": 'johndoe@netsach.org', "password": "plop",},
        )

        # print(resp.status_code)
        self.assertEqual(
            resp.status_code, status.HTTP_200_OK, msg=resp.content
        )
        token = resp.data['token']

        # With another client
        client = Client()

        # Use without token to access the url_that_required_auth (401)
        resp = client.post(url_that_require_auth)
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

        # Use with stolen token to access the url_that_required_auth (200)
        resp = client.post(
            url_that_require_auth, HTTP_AUTHORIZATION='Token {}'.format(token)
        )

        self.assertNotIn(
            resp.status_code,
            [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN],
        )

    def test_basic_authentication_error_cases(self):
        """
        Test basic auth workflow
        """
        url = '/api/v1.1/auth/login/'

        # POST an invalid arguimentsand get an error (400)
        resp = self.client.post(url, {"email": 'johndoe@netsach.org'})
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('_errors', resp.data)
        self.assertEqual(resp.data['_errors'], ['INVALID_DATA'])

        # POST an invalid email and get an error (400)
        resp = self.client.post(
            url, {"email": 'johndoeXXXX', "password": "wrong-password"}
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('_errors', resp.data)
        self.assertEqual(resp.data['_errors'], ['INVALID_DATA'])

        # POST an unknown email and get an error (401)
        resp = self.client.post(
            url, {"email": 'johndoe2@netsach.org', "password": "some-password"}
        )
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn('_errors', resp.data)
        self.assertEqual(resp.data['_errors'], ['WRONG_AUTH_CREDENTIALS'])

        # POST an invalid password and get an error (401)
        resp = self.client.post(
            url, {"email": 'johndoe@netsach.org', "password": "wrong-password"}
        )
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn('_errors', resp.data)
        self.assertEqual(resp.data['_errors'], ['WRONG_AUTH_CREDENTIALS'])

        # POST as a blocked user
        resp = self.client.post(
            url, {"email": 'janedoe@netsach.org', "password": "plop"}
        )
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn('_errors', resp.data)
        self.assertEqual(resp.data['_errors'], ['USER_BLOCKED'])

        # POST as a blocked user
        resp = self.client.post(
            url, {"email": 'janedoe@netsach.org', "password": "plop"}
        )
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn('_errors', resp.data)
        self.assertEqual(resp.data['_errors'], ['USER_BLOCKED'])

    @override_settings(AUTH_CONFIRM_EMAIL_ENABLE=True)
    def test_basic_auth_unconfirmed(self):
        url = '/api/v1.1/auth/login/'

        resp = self.client.post(
            url, {"email": 'juliadoe@netsach.org', "password": "plop"}
        )
        self.assertEqual(resp.status_code, status.HTTP_412_PRECONDITION_FAILED)
        self.assertIn('_errors', resp.data)
        self.assertEqual(resp.data['_errors'], ['EMAIL_NOT_VALIDATED'])

    @patch('concrete_datastore.api.v1.views.authenticate')
    @override_settings(PASSWORD_EXPIRY_TIME=1)
    def test_basic_auth_password_expired(self, mock_auth):
        url = '/api/v1.1/auth/login/'

        User = get_user_model()
        user = User.objects.create(email='joho@netsach.org')
        user.password_modification_date = date.today() - timedelta(days=2)
        mock_auth.return_value = user

        resp = self.client.post(
            url, {"email": 'joho@netsach.org', "password": "plop"}
        )
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn('_errors', resp.data)
        self.assertEqual(resp.data['_errors'], ['EXPIRED_PASSWORD'])
