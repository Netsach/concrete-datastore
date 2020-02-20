# coding: utf-8
from rest_framework.test import APITestCase
from rest_framework import status
from concrete_datastore.concrete.models import (
    User,
    UserConfirmation,
    ConcretePermission,
)
import warnings
from django.test import override_settings


@override_settings(DEBUG=True)
class RedirectionForDepricatedRolesView(APITestCase):
    def setUp(self):
        self.deprecated_permission_url = '/api/v1.1/concrete-permission/'
        self.superuser = User.objects.create_user('superuser@netsach.org')
        self.superuser.set_password('plop')
        self.superuser.set_level('superuser')
        self.superuser.save()
        # User 1 auth
        UserConfirmation.objects.create(
            user=self.superuser, confirmed=True
        ).save()

        url = '/api/v1.1/auth/login/'
        resp = self.client.post(
            url, {"email": "superuser@netsach.org", "password": "plop"}
        )
        self.token_superuser = resp.data['token']

        permission = ConcretePermission.objects.create(
            model_name='Permission 1'
        )
        self.permission_uid = permission.uid
        warnings.simplefilter("always")

    def test_get_view_with_redirect(self):
        with warnings.catch_warnings(record=True) as w:
            resp = self.client.get(
                self.deprecated_permission_url,
                HTTP_AUTHORIZATION='Token {}'.format(self.token_superuser),
            )

            self.assertEqual(resp.status_code, status.HTTP_200_OK)
            resp = self.client.get(
                f'{self.deprecated_permission_url}{self.permission_uid}/',
                HTTP_AUTHORIZATION='Token {}'.format(self.token_superuser),
            )

            self.assertEqual(resp.status_code, status.HTTP_200_OK)

            self.assertEqual(len(w), 2)
            self.assertTrue(issubclass(w[0].category, DeprecationWarning))
            self.assertTrue(issubclass(w[1].category, DeprecationWarning))

    def test_post_view_with_bad_request(self):
        with warnings.catch_warnings(record=True) as w:
            resp = self.client.post(
                self.deprecated_permission_url,
                {'model_name': 'PermissionName'},
                HTTP_AUTHORIZATION='Token {}'.format(self.token_superuser),
            )

            self.assertEqual(len(w), 1)
            self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

            resp = self.client.patch(
                f'{self.deprecated_permission_url}{self.permission_uid}/',
                {'model_name': 'ManagerPermission'},
                HTTP_AUTHORIZATION='Token {}'.format(self.token_superuser),
            )

            self.assertEqual(len(w), 3)
            self.assertEqual(resp.status_code, status.HTTP_200_OK)

            resp = self.client.put(
                f'{self.deprecated_permission_url}{self.permission_uid}/',
                {'model_name': 'ManagerPermission'},
                HTTP_AUTHORIZATION='Token {}'.format(self.token_superuser),
            )

            self.assertEqual(len(w), 5)
            self.assertEqual(resp.status_code, status.HTTP_200_OK)

            resp = self.client.delete(
                f'{self.deprecated_permission_url}{self.permission_uid}/',
                {'model_name': 'ManagerPermission'},
                HTTP_AUTHORIZATION='Token {}'.format(self.token_superuser),
            )

            self.assertEqual(len(w), 6)
            self.assertEqual(
                resp.status_code, status.HTTP_405_METHOD_NOT_ALLOWED
            )

            self.assertTrue(issubclass(w[0].category, DeprecationWarning))
            self.assertTrue(issubclass(w[1].category, DeprecationWarning))
            self.assertTrue(issubclass(w[2].category, DeprecationWarning))
            self.assertTrue(issubclass(w[3].category, DeprecationWarning))
            self.assertTrue(issubclass(w[4].category, DeprecationWarning))
            self.assertTrue(issubclass(w[5].category, DeprecationWarning))
