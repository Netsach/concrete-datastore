# coding: utf-8
from rest_framework.test import APITestCase
from rest_framework import status
from django.test import override_settings
from concrete_datastore.concrete.models import (
    User,
    UserConfirmation,
    DefaultDivider,
)


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
            url, {"email": "admin@netsach.org", "password": "plop"}
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
            url, {"email": "simple@netsach.org", "password": "plop"}
        )
        self.token_simple = resp.data['token']

    def test_simple_user_cannot_change_his_level(self):
        url_user_simple = '/api/v1.1/user/{}/'.format(self.user_simple.uid)
        resp = self.client.patch(
            url_user_simple,
            {"level": "admin"},
            HTTP_AUTHORIZATION='Token {}'.format(self.token_simple),
        )
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

        url_user_simple = '/api/v1.1/account/me/'
        resp = self.client.patch(
            url_user_simple,
            {"level": "admin"},
            HTTP_AUTHORIZATION='Token {}'.format(self.token_simple),
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['level'], 'SimpleUser')

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


class RetrieveUsersTestCase(APITestCase):
    def test_user_get_permissions(self):
        divider = DefaultDivider.objects.create(name="TEST1")
        simple = User.objects.create(email='simple@netsach.org')
        simple.defaultdividers.add(divider)
        token_simple = simple.auth_tokens.create().key
        manager = User.objects.create(email='manager@netsach.org')
        manager.defaultdividers.add(divider)
        token_manager = manager.auth_tokens.create().key
        manager.set_level('manager')
        manager.save()
        admin = User.objects.create(email='admin@netsach.org')
        admin.defaultdividers.add(divider)
        token_admin = admin.auth_tokens.create().key
        admin.set_level('admin')
        admin.save()
        superuser = User.objects.create(email='superuser@netsach.org')
        superuser.defaultdividers.add(divider)
        token_superuser = superuser.auth_tokens.create().key
        superuser.set_level('superuser')
        superuser.save()
        #: Unscoped requests
        #: The simple user cannot acces to any of the users. expect a 403
        resp = self.client.get(
            '/api/v1.1/user/',
            HTTP_AUTHORIZATION='Token {}'.format(token_simple),
        )
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)
        resp = self.client.get(
            f'/api/v1.1/user/{admin.pk}/',
            HTTP_AUTHORIZATION='Token {}'.format(token_simple),
        )
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)
        #: The manager has access to all users
        resp = self.client.get(
            '/api/v1.1/user/',
            HTTP_AUTHORIZATION='Token {}'.format(token_manager),
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['total_objects_count'], 4)
        resp = self.client.get(
            f'/api/v1.1/user/{admin.pk}/',
            HTTP_AUTHORIZATION='Token {}'.format(token_manager),
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        #: The admin has access to all users
        resp = self.client.get(
            '/api/v1.1/user/',
            HTTP_AUTHORIZATION='Token {}'.format(token_admin),
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['total_objects_count'], 4)
        #: The superuser has access to all users
        resp = self.client.get(
            '/api/v1.1/user/',
            HTTP_AUTHORIZATION='Token {}'.format(token_superuser),
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['total_objects_count'], 4)

        #: Scoped requests
        #: The simple user cannot acces to any of the users. expect a 403
        resp = self.client.get(
            '/api/v1.1/user/',
            HTTP_AUTHORIZATION='Token {}'.format(token_simple),
            HTTP_X_ENTITY_UID=str(divider.uid),
        )
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)
        resp = self.client.get(
            f'/api/v1.1/user/{admin.pk}/',
            HTTP_AUTHORIZATION='Token {}'.format(token_simple),
            HTTP_X_ENTITY_UID=str(divider.uid),
        )
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)
        #: The manager cannot acces to any of the users. expect a 403
        resp = self.client.get(
            '/api/v1.1/user/',
            HTTP_AUTHORIZATION='Token {}'.format(token_manager),
            HTTP_X_ENTITY_UID=str(divider.uid),
        )
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)
        resp = self.client.get(
            f'/api/v1.1/user/{admin.pk}/',
            HTTP_AUTHORIZATION='Token {}'.format(token_manager),
            HTTP_X_ENTITY_UID=str(divider.uid),
        )
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)
        #: The admin has access to all users
        resp = self.client.get(
            '/api/v1.1/user/',
            HTTP_AUTHORIZATION='Token {}'.format(token_admin),
            HTTP_X_ENTITY_UID=str(divider.uid),
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['total_objects_count'], 4)
        #: The superuser has access to all users
        resp = self.client.get(
            '/api/v1.1/user/',
            HTTP_AUTHORIZATION='Token {}'.format(token_superuser),
            HTTP_X_ENTITY_UID=str(divider.uid),
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['total_objects_count'], 4)
