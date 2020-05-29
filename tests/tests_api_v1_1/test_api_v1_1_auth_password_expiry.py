# coding: utf-8
from rest_framework.test import APITestCase
from rest_framework import status
from django.test import override_settings
from concrete_datastore.concrete.models import User, UserConfirmation
from datetime import timedelta


@override_settings(DEBUG=True)
class PasswordExpiryTestCase(APITestCase):
    def setUp(self):
        # Create a user
        self.user = User.objects.create_user(
            email='johndoe@netsach.org', password='plop'
        )
        self.user.password_modification_date += timedelta(-5)
        self.user.save()
        self.confirmation = UserConfirmation.objects.create(user=self.user)
        self.confirmation.confirmed = True
        self.confirmation.save()

    # Set expiry to 3 days
    @override_settings(PASSWORD_EXPIRY_TIME=3)
    def test_password_expiry(self):
        """
        Test basic auth workflow
        """
        url = '/api/v1.1/auth/login/'
        url_change_password = '/api/v1.1/auth/change-password/'
        url_that_require_auth = '/api/v1.1/project/'

        # Ensure that a unauthenticated user cannot access the view (401)
        resp = self.client.post(url_that_require_auth)
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

        # POST a valid user/password and get a session ID (200)
        resp = self.client.post(
            url, {"email": 'johndoe@netsach.org', "password": "plop"}
        )
        self.assertEqual(
            resp.status_code, status.HTTP_403_FORBIDDEN, msg=resp.content
        )
        self.assertIn('message_en', resp.data)
        self.assertIn('message_fr', resp.data)
        self.assertIn('_errors', resp.data)
        self.assertIn('email', resp.data)
        self.assertIn('password_change_token', resp.data)
        email = resp.data.get('email')
        password_change_token = resp.data.get('password_change_token')

        resp = self.client.post(
            url_change_password,
            {
                "email": email,
                "password_change_token": password_change_token,
                "password1": "new_password",
                "password2": "new_password",
            },
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn('token', resp.data)
        self.assertIn('email', resp.data)
        self.assertIn('first_name', resp.data)
        self.assertIn('last_name', resp.data)
        self.assertIn('email', resp.data)

    # Set expiry to 3 days
    @override_settings(PASSWORD_EXPIRY_TIME=3)
    def test_password_expiry_same_password(self):
        """
        Test basic auth workflow
        """
        url = '/api/v1.1/auth/login/'
        url_change_password = '/api/v1.1/auth/change-password/'
        url_that_require_auth = '/api/v1.1/project/'

        # Ensure that a unauthenticated user cannot access the view (401)
        resp = self.client.post(url_that_require_auth)
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

        # POST a valid user/password and get a session ID (200)
        resp = self.client.post(
            url, {"email": 'johndoe@netsach.org', "password": "plop"}
        )
        self.assertEqual(
            resp.status_code, status.HTTP_403_FORBIDDEN, msg=resp.content
        )
        self.assertIn('message_en', resp.data)
        self.assertIn('message_fr', resp.data)
        self.assertIn('_errors', resp.data)
        self.assertIn('email', resp.data)
        self.assertIn('password_change_token', resp.data)
        email = resp.data.get('email')
        password_change_token = resp.data.get('password_change_token')

        resp = self.client.post(
            url_change_password,
            {
                "email": email,
                "password_change_token": password_change_token,
                "password1": "plop",
                "password2": "plop",
            },
        )
        self.assertEqual(
            resp.status_code, status.HTTP_400_BAD_REQUEST, msg=resp.content
        )
        self.assertIn('message', resp.data)
        self.assertEqual(
            resp.data['message'], 'New password must be different'
        )

    # Set expiry to 10 days
    @override_settings(PASSWORD_EXPIRY_TIME=10)
    def test_password_not_expired(self):
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
            url, {"email": 'johndoe@netsach.org', "password": "plop"}
        )
        self.assertEqual(
            resp.status_code, status.HTTP_200_OK, msg=resp.content
        )
        self.assertIn('token', resp.data)
