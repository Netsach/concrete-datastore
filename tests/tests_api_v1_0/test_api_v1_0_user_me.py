# coding: utf-8
from rest_framework.test import APITestCase
from rest_framework import status
from concrete_datastore.concrete.models import User, UserConfirmation
from django.test import override_settings


@override_settings(DEBUG=True)
class UserAllTestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            'johndoe@netsach.org',
            # 'John',
            # 'Doe',
        )
        self.user.set_password('plop')
        self.user.save()
        # User 1 auth
        UserConfirmation.objects.create(user=self.user, confirmed=True).save()
        url = '/api/v1/auth/login/'
        resp = self.client.post(
            url,
            {
                # "username": 'johndoe@netsach.org',
                "email": "johndoe@netsach.org",
                "password": "plop",
            },
        )
        self.token = resp.data['token']

    def test_get_user(self):
        url = '/api/v1/account/me/'
        resp = self.client.get(
            url, HTTP_AUTHORIZATION='Token {}'.format(self.token)
        )
        self.assertEqual(resp.data['email'], 'johndoe@netsach.org')
        self.assertEqual('is_staff' not in resp.data, True)
        self.assertEqual('admin' not in resp.data, True)
        self.assertEqual('verbose_name' in resp.data, True)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
