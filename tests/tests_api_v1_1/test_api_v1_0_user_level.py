# coding: utf-8
from rest_framework.test import APITestCase
from rest_framework import status
from django.test import override_settings
from concrete_datastore.concrete.models import User, UserConfirmation


@override_settings(DEBUG=True)
class UserTestCase(APITestCase):
    def setUp(self):
        self.user_admin = User.objects.create_user('admin@netsach.org')
        self.user_admin.set_password('plop')
        confirmation = UserConfirmation.objects.create(user=self.user_admin)
        confirmation.confirmed = True
        confirmation.save()
        self.user_admin.confirmed = True
        self.user_admin.level = "admin"
        self.user_admin.save()
        self.assertEqual(self.user_admin.admin, True)
        url = '/api/v1.1/auth/login/'
        resp = self.client.post(
            url,
            {
                "email": "admin@netsach.org",
                "password": "plop",
            },
        )
        self.token_admin = resp.data['token']

        self.user_simple = User.objects.create_user('simple@netsach.org')
        self.user_simple.set_password('plop')
        confirmation = UserConfirmation.objects.create(user=self.user_simple)
        confirmation.confirmed = True
        confirmation.save()
        self.user_simple.confirmed = True
        self.user_simple.level = "simpleuser"
        self.assertEqual(self.user_simple.admin, False)
        self.assertEqual(self.user_simple.is_staff, False)
        self.user_simple.save()

        url = '/api/v1.1/auth/login/'
        resp = self.client.post(
            url,
            {
                "email": "simple@netsach.org",
                "password": "plop",
            },
        )
        self.token_simple = resp.data['token']

    def test_simple_user_cannot_change_his_level(self):
        url_user_simple = '/api/v1.1/user/{}/'.format(self.user_simple.uid)
        resp = self.client.patch(
            url_user_simple,
            {"level": "admin"},
            HTTP_AUTHORIZATION='Token {}'.format(self.token_simple),
        )
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_admin_user_can_elevate_simple_to_manager(self):
        url_user_simple = '/api/v1.1/user/{}/'.format(self.user_simple.uid)
        resp = self.client.patch(
            url_user_simple,
            {"level": "manager"},
            HTTP_AUTHORIZATION='Token {}'.format(self.token_admin),
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data.get('level'), "manager")
        self.assertEqual(resp.data.get('is_staff'), True)

    def test_admin_user_cannot_elevate_simple_to_admin(self):
        url_user_simple = '/api/v1.1/user/{}/'.format(self.user_simple.uid)
        resp = self.client.patch(
            url_user_simple,
            {"level": "admin"},
            HTTP_AUTHORIZATION='Token {}'.format(self.token_admin),
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        u = User.objects.get(uid=self.user_simple.uid)
        self.assertEqual(u.level, "simpleuser")
        self.assertEqual(u.admin, False)

    def test_admin_user_cannot_elevate_simple_to_superuser(self):
        url_user_simple = '/api/v1.1/user/{}/'.format(self.user_simple.uid)
        resp = self.client.patch(
            url_user_simple,
            {"level": "superuser"},
            HTTP_AUTHORIZATION='Token {}'.format(self.token_admin),
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        u = User.objects.get(uid=self.user_simple.uid)
        self.assertEqual(u.level, "simpleuser")
        self.assertEqual(u.is_superuser, False)
