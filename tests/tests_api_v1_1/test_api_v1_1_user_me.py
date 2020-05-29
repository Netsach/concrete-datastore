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
        url = '/api/v1.1/auth/login/'
        resp = self.client.post(
            url,
            {
                "email": "johndoe@netsach.org",
                "password": "plop",
            },
        )
        self.token = resp.data['token']

    def test_get_user(self):
        url = '/api/v1.1/account/me/'
        resp = self.client.get(
            url, HTTP_AUTHORIZATION='Token {}'.format(self.token)
        )
        self.assertEqual(resp.data['email'], 'johndoe@netsach.org')
        self.assertEqual('is_staff' not in resp.data, True)
        self.assertEqual('admin' not in resp.data, True)
        self.assertEqual('verbose_name' in resp.data, True)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    # def test_try_alter_user_account_me(self):
    #     url = '/api/v1.1/account/me/'

    #     resp = self.client.patch(
    #         url,
    #         {
    #             "email": 'janedoe@netsach.org',
    #         },
    #         HTTP_AUTHORIZATION='Token {}'.format(self.token)
    #     )
    #     self.assertEqual(resp.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    #     resp = self.client.post(
    #         url,
    #         {
    #             "email": "johndoe@netsach.org",
    #             "password": "plop",
    #             "is_staff": True,
    #             "admin": True,
    #             "verbose_name": "piou"
    #         },
    #         HTTP_AUTHORIZATION='Token {}'.format(self.token)
    #     )

    #     self.assertEqual(resp.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
    #     resp = self.client.put(
    #         url,
    #         {
    #             "email": "johndoe@netsach.org",
    #             "password": "plop",
    #             "is_staff": True,
    #             "admin": True,
    #             "verbose_name": "piou"
    #         },
    #         HTTP_AUTHORIZATION='Token {}'.format(self.token)
    #     )
    #     self.assertEqual(resp.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
