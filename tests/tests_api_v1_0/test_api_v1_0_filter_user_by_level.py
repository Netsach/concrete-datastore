# coding: utf-8
from rest_framework.test import APITestCase
from rest_framework import status
from django.test import override_settings
from concrete_datastore.concrete.models import User, UserConfirmation


@override_settings(DEBUG=True)
class UserLevelFilteringTestCase(APITestCase):
    def setUp(self):
        # superuser
        self.user_superuser = User.objects.create_user('superuser@netsach.org')
        self.user_superuser.set_password('plop')
        self.user_superuser.confirmed = True
        confirmation = UserConfirmation.objects.create(
            user=self.user_superuser
        )
        confirmation.confirmed = True
        confirmation.save()
        self.user_superuser.set_level("superuser")
        self.user_superuser.save()

        # admin
        self.user_admin = User.objects.create_user('admin@netsach.org')
        self.user_admin.set_password('plop')
        self.user_admin.confirmed = True
        confirmation = UserConfirmation.objects.create(user=self.user_admin)
        confirmation.confirmed = True
        confirmation.save()
        self.user_admin.set_level("admin")
        self.user_admin.save()

        # manager
        self.user_manager = User.objects.create_user('manager@netsach.org')
        self.user_manager.set_password('plop')
        self.user_manager.confirmed = True
        confirmation = UserConfirmation.objects.create(user=self.user_manager)
        confirmation.confirmed = True
        confirmation.save()
        self.user_manager.set_level("manager")
        self.user_manager.save()

        # simpleuser
        self.user_simpleuser = User.objects.create_user(
            'simpleuser@netsach.org'
        )
        self.user_simpleuser.set_password('plop')
        self.user_simpleuser.confirmed = True
        confirmation = UserConfirmation.objects.create(
            user=self.user_simpleuser
        )
        confirmation.confirmed = True
        confirmation.save()
        self.user_simpleuser.set_level("simpleuser")
        self.user_simpleuser.save()

        # blocked
        self.user_blocked = User.objects.create_user('blocked@netsach.org')
        self.user_blocked.set_password('plop')
        self.user_blocked.confirmed = True
        confirmation = UserConfirmation.objects.create(user=self.user_blocked)
        confirmation.confirmed = True
        confirmation.save()
        self.user_blocked.set_level("blocked")
        self.user_blocked.save()
        url = '/api/v1/auth/login/'
        resp = self.client.post(
            url,
            {
                # "username": 'johndoe@netsach.org',
                "email": "superuser@netsach.org",
                "password": "plop",
            },
        )
        self.token = resp.data['token']

    def test_filter_equals(self):
        url_user = '/api/v1/user/?level={}'
        resp = self.client.get(
            url_user.format('manager'),
            HTTP_AUTHORIZATION='Token {}'.format(self.token),
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['objects_count'], 1)

        resp = self.client.get(
            url_user.format('wrong_level'),
            HTTP_AUTHORIZATION='Token {}'.format(self.token),
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['objects_count'], 0)

    def test_filter_atleast(self):
        url_user = '/api/v1/user/?atleast={}'
        resp = self.client.get(
            url_user.format('manager'),
            HTTP_AUTHORIZATION='Token {}'.format(self.token),
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['objects_count'], 3)

        resp = self.client.get(
            url_user.format('superuser'),
            HTTP_AUTHORIZATION='Token {}'.format(self.token),
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['objects_count'], 1)

        resp = self.client.get(
            url_user.format('blocked'),
            HTTP_AUTHORIZATION='Token {}'.format(self.token),
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['objects_count'], 0)
