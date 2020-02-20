# coding: utf-8
from rest_framework.test import APITestCase
from rest_framework import status
from concrete_datastore.concrete.models import (
    User,
    UserConfirmation,
    ConcretePermission,
    ConcreteRole,
    RoleModel,
)
from django.test import override_settings


@override_settings(USE_CONCRETE_ROLES=True)
class CRUDTestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            'johndoe@netsach.org'
            # 'John',
            # 'Doe',
        )
        self.user.set_password('plop')
        self.user.set_level('manager')
        self.user.save()
        self.confirmation = UserConfirmation.objects.create(user=self.user)
        self.confirmation.confirmed = True
        self.confirmation.save()
        url = '/api/v1.1/auth/login/'
        resp = self.client.post(
            url, {"email": "johndoe@netsach.org", "password": "plop"}
        )
        self.token = resp.data['token']

        self.role_CRUD = ConcreteRole.objects.create(name="updater")
        target_model_permission, _ = ConcretePermission.objects.get_or_create(
            model_name="RoleModel"
        )

        target_model_permission.create_roles.add(self.role_CRUD)
        target_model_permission.retrieve_roles.add(self.role_CRUD)
        target_model_permission.update_roles.add(self.role_CRUD)
        target_model_permission.delete_roles.add(self.role_CRUD)
        target_model_permission.save()

        self.role_model_1 = RoleModel.objects.create(name="instance1")

    def test_create_role(self):

        url_role_model = '/api/v1.1/role-model/'

        # Get without having the role
        resp = self.client.post(
            url_role_model,
            {"name": "instance 2"},
            HTTP_AUTHORIZATION='Token {}'.format(self.token),
        )

        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

        self.role_CRUD.users.add(self.user)

        resp = self.client.post(
            url_role_model,
            {"name": "instance 2"},
            HTTP_AUTHORIZATION='Token {}'.format(self.token),
        )

        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(resp.data['name'], 'instance 2')

        url_created = resp.data['url']
        self.role_model_1.can_view_users.add(self.user)
        resp = self.client.get(
            url_created, {}, HTTP_AUTHORIZATION='Token {}'.format(self.token)
        )
        # Get works because instance was created by the user
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_retrieve_role(self):

        url_role_model = '/api/v1.1/role-model/'

        # Get without having the role
        resp = self.client.get(
            url_role_model,
            {},
            HTTP_AUTHORIZATION='Token {}'.format(self.token),
        )

        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

        self.role_CRUD.users.add(self.user)

        # Get with the role
        resp = self.client.get(
            url_role_model,
            {},
            HTTP_AUTHORIZATION='Token {}'.format(self.token),
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.data['results']), 0)

        # Get with the role and can_view

        self.role_model_1.can_view_users.add(self.user)
        resp = self.client.get(
            url_role_model,
            {},
            HTTP_AUTHORIZATION='Token {}'.format(self.token),
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.data['results']), 1)

        self.role_model_1.can_view_users.add(self.user)
        resp = self.client.get(
            url_role_model + str(self.role_model_1.uid) + '/',
            {},
            HTTP_AUTHORIZATION='Token {}'.format(self.token),
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_update_role(self):

        url_role_model = '/api/v1.1/role-model/'

        # Without the role
        resp = self.client.patch(
            url_role_model + str(self.role_model_1.uid) + '/',
            {"name": "NewName"},
            HTTP_AUTHORIZATION='Token {}'.format(self.token),
        )
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

        self.role_CRUD.users.add(self.user)

        # With the role but not in can admin
        resp = self.client.patch(
            url_role_model + str(self.role_model_1.uid) + '/',
            {"name": "NewName"},
            HTTP_AUTHORIZATION='Token {}'.format(self.token),
        )
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

        # With the role and in can admin
        self.role_model_1.can_admin_users.add(self.user)
        resp = self.client.patch(
            url_role_model + str(self.role_model_1.uid) + '/',
            {"name": "NewName"},
            HTTP_AUTHORIZATION='Token {}'.format(self.token),
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['name'], "NewName")
