# coding: utf-8
from rest_framework.test import APITestCase
from rest_framework import status
from concrete_datastore.concrete.models import User, UserConfirmation
from django.test import override_settings


@override_settings(DEBUG=True)
class AuthTestCase(APITestCase):
    def setUp(self):
        # Create a user
        self.user = User.objects.create_user(
            email='johndoe@netsach.org',
            password='plop'
            # 'John',
            # 'Doe',
        )
        self.user.save()
        self.confirmation = UserConfirmation.objects.create(
            user=self.user, redirect_to=None
        )
        self.confirmation.save()

    @override_settings(AUTH_CONFIRM_EMAIL_ENABLE=True)
    def test_cannot_login(self):
        url = '/api/v1/auth/login/'

        # POST a valid user/password and get a session ID (200)
        resp = self.client.post(
            url,
            {
                # "username": 'test-username',
                "email": 'johndoe@netsach.org',
                "password": "plop",
            },
        )
        self.assertEqual(
            resp.status_code,
            status.HTTP_412_PRECONDITION_FAILED,
            msg=resp.content,
        )
        self.assertDictEqual(
            resp.data,
            {
                'message': 'Email has not been validated',
                "_errors": ["EMAIL_NOT_VALIDATED"],
            },
        )

    def test_mail_confirmed(self):
        confirmation_uid = self.confirmation.uid
        confirmation_url = '/c/confirm-user-email/{}'.format(confirmation_uid)

        resp = self.client.get(confirmation_url)
        url = '/api/v1/auth/login/'
        # POST a valid user/password and get a session ID (200)
        resp = self.client.post(
            url,
            {
                # "username": 'test-username',
                "email": 'johndoe@netsach.org',
                "password": "plop",
            },
        )
        self.assertEqual(
            resp.status_code, status.HTTP_200_OK, msg=resp.content
        )
        self.assertIn('token', resp.data)
        self.assertIn('email', resp.data)
        self.assertIn('first_name', resp.data)
        self.assertIn('last_name', resp.data)
        self.assertIn('uid', resp.data)

    def test_mail_confirmed_with_redirection(self):
        self.confirmation.redirect_to = "http://httpstat.us/200"
        self.confirmation.send_link()
        self.confirmation.save()
        confirmation_url = '/c/confirm-user-email/{}'.format(
            self.confirmation.uid
        )
        self.client.get(confirmation_url)
