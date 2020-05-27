# coding: utf-8
from rest_framework.test import APITestCase
from rest_framework import status
from concrete_datastore.concrete.models import User, UserConfirmation, Crud
from django.test import override_settings


@override_settings(DEBUG=True)
class CreationMinimumLevelTestCase(APITestCase):
    def setUp(self):

        # USER ADMIN
        self.user_admin = User.objects.create_user('admin@netsach.org')
        self.user_admin.set_password('plop')
        self.user_admin.admin = True
        self.user_admin.save()
        confirmation = UserConfirmation.objects.create(
            user=self.user_admin, confirmed=True
        )
        confirmation.save()
        url = '/api/v1.1/auth/login/'
        resp = self.client.post(
            url, {"email": "admin@netsach.org", "password": "plop"}
        )
        self.token_admin = resp.data['token']

        # USER NON ADMIN
        self.user_non_admin = User.objects.create_user('user@netsach.org')
        self.user_non_admin.set_password('plop')
        self.user_non_admin.save()
        confirmation = UserConfirmation.objects.create(
            user=self.user_non_admin, confirmed=True
        )
        confirmation.save()
        url = '/api/v1.1/auth/login/'
        resp = self.client.post(
            url, {"email": "user@netsach.org", "password": "plop"}
        )
        self.token_non_admin = resp.data['token']

        # USER SU
        self.user_superuser = User.objects.create_user('su@netsach.org')
        self.user_superuser.set_password('plop')
        self.user_admin.is_superuser = True
        self.user_superuser.save()
        confirmation = UserConfirmation.objects.create(
            user=self.user_superuser, confirmed=True
        )
        confirmation.save()
        url = '/api/v1.1/auth/login/'
        resp = self.client.post(
            url, {"email": "su@netsach.org", "password": "plop"}
        )
        self.token_superuser = resp.data['token']

        # URLS
        self.url_crud = '/api/v1.1/crud/'

        # Crud TEST
        resp = self.client.post(
            self.url_crud,
            {"name": "TEST"},
            HTTP_AUTHORIZATION='Token {}'.format(self.token_admin),
        )
        self.crud_test = Crud.objects.get(name="TEST")

    def test_non_admin_CRUD(self):

        resp = self.client.post(
            self.url_crud,
            {"name": "Crud1"},
            HTTP_AUTHORIZATION='Token {}'.format(self.token_non_admin),
        )
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(Crud.objects.count(), 1)

        resp = self.client.patch(
            self.url_crud + str(self.crud_test.uid) + "/",
            {"name": "TOTO"},
            HTTP_AUTHORIZATION='Token {}'.format(self.token_non_admin),
        )
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

        resp = self.client.delete(
            self.url_crud + str(self.crud_test.uid) + "/",
            HTTP_AUTHORIZATION='Token {}'.format(self.token_non_admin),
        )
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(Crud.objects.count(), 1)
        pass

    def test_admin_CRUD(self):

        resp = self.client.post(
            self.url_crud,
            {"name": "Crud1"},
            HTTP_AUTHORIZATION='Token {}'.format(self.token_admin),
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Crud.objects.count(), 2)
        self.assertIn("url", resp.data)
        url = resp.data['url']

        resp = self.client.get(
            url, HTTP_AUTHORIZATION='Token {}'.format(self.token_admin)
        )

        resp = self.client.patch(
            url,
            {"name": "TOTO"},
            HTTP_AUTHORIZATION='Token {}'.format(self.token_admin),
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        resp = self.client.delete(
            url, HTTP_AUTHORIZATION='Token {}'.format(self.token_admin)
        )
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Crud.objects.count(), 1)
        pass

    def test_unauth_CRUD(self):
        resp = self.client.post(self.url_crud, {"name": "crud1"})
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(Crud.objects.count(), 1)

        resp = self.client.patch(
            self.url_crud + str(self.crud_test.uid) + "/", {"name": "TOTO"}
        )
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

        resp = self.client.delete(
            self.url_crud + str(self.crud_test.uid) + "/"
        )
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(Crud.objects.count(), 1)
        pass
