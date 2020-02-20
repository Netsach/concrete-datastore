# coding: utf-8
from rest_framework.test import APITestCase
from rest_framework import status
from concrete_datastore.concrete.models import User, UserConfirmation
from django.test import override_settings


class GenerateTokenTestCase(APITestCase):
    def setUp(self):
        # Create a user
        self.user = User.objects.create_user('user@netsach.org')
        self.user.set_password('plop')
        self.user.set_level('superuser', commit=True)
        self.user.superuser = True
        self.user.save()
        UserConfirmation.objects.create(user=self.user, confirmed=True).save()
        self.url_login = '/api/v1.1/auth/login/'

    @override_settings(
        USE_MULTIPLE_TOKENS=True,
        SESSIONS_NUMBER_CONTROL_ENABLED=True,
        MAX_SIMULTANEOUS_SESSIONS=1,
    )
    def test_disabled_simultaneous_sessions(self):
        url_that_require_auth = '/api/v1.1/project/'
        resp = self.client.post(
            self.url_login, {"email": "user@netsach.org", "password": "plop"}
        )
        first_token = resp.data['token']
        resp = self.client.get(
            url_that_require_auth,
            HTTP_AUTHORIZATION='Token {}'.format(first_token),
        )
        self.assertEqual(
            resp.status_code, status.HTTP_200_OK, msg=resp.content
        )

        resp = self.client.post(
            self.url_login, {"email": "user@netsach.org", "password": "plop"}
        )
        second_token = resp.data['token']
        self.assertNotEqual(first_token, second_token)
        resp = self.client.get(
            url_that_require_auth,
            HTTP_AUTHORIZATION='Token {}'.format(second_token),
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        resp = self.client.get(
            url_that_require_auth,
            HTTP_AUTHORIZATION='Token {}'.format(first_token),
        )
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    @override_settings(
        USE_MULTIPLE_TOKENS=True, SESSIONS_NUMBER_CONTROL_ENABLED=False
    )
    def test_enabled_simultaneous_sessions(self):
        url_that_require_auth = '/api/v1.1/project/'
        resp = self.client.post(
            self.url_login, {"email": "user@netsach.org", "password": "plop"}
        )
        first_token = resp.data['token']
        resp = self.client.get(
            url_that_require_auth,
            HTTP_AUTHORIZATION='Token {}'.format(first_token),
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        resp = self.client.post(
            self.url_login, {"email": "user@netsach.org", "password": "plop"}
        )
        second_token = resp.data['token']
        resp = self.client.get(
            url_that_require_auth,
            HTTP_AUTHORIZATION='Token {}'.format(second_token),
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        resp = self.client.get(
            url_that_require_auth,
            HTTP_AUTHORIZATION='Token {}'.format(first_token),
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    @override_settings(
        USE_MULTIPLE_TOKENS=False, SESSIONS_NUMBER_CONTROL_ENABLED=True
    )
    def test_disabled_simultaneous_sessions_and_no_multiple_tokens(self):
        url_that_require_auth = '/api/v1.1/project/'
        resp = self.client.post(
            self.url_login, {"email": "user@netsach.org", "password": "plop"}
        )
        first_token = resp.data['token']
        resp = self.client.get(
            url_that_require_auth,
            HTTP_AUTHORIZATION='Token {}'.format(first_token),
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        resp = self.client.post(
            self.url_login, {"email": "user@netsach.org", "password": "plop"}
        )
        second_token = resp.data['token']
        resp = self.client.get(
            url_that_require_auth,
            HTTP_AUTHORIZATION='Token {}'.format(second_token),
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        resp = self.client.get(
            url_that_require_auth,
            HTTP_AUTHORIZATION='Token {}'.format(first_token),
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(first_token, second_token)

    @override_settings(
        USE_MULTIPLE_TOKENS=False, SESSIONS_NUMBER_CONTROL_ENABLED=False
    )
    def test_enabled_simultaneous_sessions_and_allowed_multiple_tokens(self):
        url_that_require_auth = '/api/v1.1/project/'
        resp = self.client.post(
            self.url_login, {"email": "user@netsach.org", "password": "plop"}
        )
        first_token = resp.data['token']
        resp = self.client.get(
            url_that_require_auth,
            HTTP_AUTHORIZATION='Token {}'.format(first_token),
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        resp = self.client.post(
            self.url_login, {"email": "user@netsach.org", "password": "plop"}
        )
        second_token = resp.data['token']
        resp = self.client.get(
            url_that_require_auth,
            HTTP_AUTHORIZATION='Token {}'.format(second_token),
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        resp = self.client.get(
            url_that_require_auth,
            HTTP_AUTHORIZATION='Token {}'.format(first_token),
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(first_token, second_token)
