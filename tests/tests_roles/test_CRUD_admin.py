# coding: utf-8
from rest_framework.test import APITestCase
from rest_framework import status
from concrete_datastore.concrete.models import (
    User,
    UserConfirmation,
    ConcretePermission,
    ConcreteRole,
    Project,
    DefaultDivider,
)
from django.test import override_settings

"""
Admins are above roles so every operations should work
"""


@override_settings(USE_CONCRETE_ROLES=True)
class CRUDTestCaseWithoutScope(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            'johndoe@netsach.org'
            # 'John',
            # 'Doe',
        )
        self.admin.set_password('plop')
        self.admin.set_level('admin')
        self.admin.save()
        self.confirmation = UserConfirmation.objects.create(user=self.admin)
        self.confirmation.confirmed = True
        self.confirmation.save()
        url = '/api/v1.1/auth/login/'
        resp = self.client.post(
            url, {"email": "johndoe@netsach.org", "password": "plop"}
        )
        self.token = resp.data['token']

        # Add one role to the user
        self.role_1 = ConcreteRole.objects.create(name="role_1")
        self.role_1.users.add(self.admin)

        # Create the permission linked to the Project
        self.target_model_permission, _ = ConcretePermission.objects.get_or_create(
            model_name="Project"
        )

        self.project_1 = Project.objects.create(name="instance1")

    def test_create_role_wo_scope(self):
        url_role_model = '/api/v1.1/project/'

        # Post without the role in the permission
        resp = self.client.post(
            url_role_model,
            {'name': 'instance2'},
            HTTP_AUTHORIZATION='Token {}'.format(self.token),
        )

        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(resp.data['name'], 'instance2')
        self.assertEqual(Project.objects.count(), 2)

        self.target_model_permission.create_roles.add(self.role_1)

        # Post with the role
        resp = self.client.post(
            url_role_model,
            {'name': 'instance3'},
            HTTP_AUTHORIZATION='Token {}'.format(self.token),
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(resp.data['name'], 'instance3')
        self.assertEqual(Project.objects.count(), 3)

    def test_retrieve_role_wo_scope(self):
        url_role_model = '/api/v1.1/project/'

        # Get without the role in the permission
        resp = self.client.get(
            url_role_model,
            {},
            HTTP_AUTHORIZATION='Token {}'.format(self.token),
        )

        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        self.target_model_permission.retrieve_roles.add(self.role_1)
        # Get with the role
        resp = self.client.get(
            url_role_model,
            {},
            HTTP_AUTHORIZATION='Token {}'.format(self.token),
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.data['results']), 1)

        # Get with the role

        resp = self.client.get(
            url_role_model,
            {},
            HTTP_AUTHORIZATION='Token {}'.format(self.token),
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.data['results']), 1)

        resp = self.client.get(
            '{}{}/'.format(url_role_model, str(self.project_1.uid)),
            HTTP_AUTHORIZATION='Token {}'.format(self.token),
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['name'], 'instance1')

    def test_update_role_wo_scope(self):
        url_role_model = '/api/v1.1/project/'
        self.project_1.can_admin_users.add(self.admin)
        # Patch without the role in the permission
        resp = self.client.patch(
            '{}{}/'.format(url_role_model, str(self.project_1.uid)),
            {'name': 'New Instance Name'},
            HTTP_AUTHORIZATION='Token {}'.format(self.token),
        )

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.project_1.refresh_from_db()
        self.assertEqual(self.project_1.name, 'New Instance Name')

        # Patch with the role
        self.target_model_permission.update_roles.add(self.role_1)
        resp = self.client.patch(
            '{}{}/'.format(url_role_model, str(self.project_1.uid)),
            {'name': 'New Instance Name 2'},
            HTTP_AUTHORIZATION='Token {}'.format(self.token),
        )
        self.assertEqual(
            resp.status_code, status.HTTP_200_OK, msg=resp.content
        )
        self.project_1.refresh_from_db()
        self.assertEqual(self.project_1.name, 'New Instance Name 2')

    def test_delete_role_wo_scope(self):
        url_role_model = '/api/v1.1/project/'
        self.project_1.can_admin_users.add(self.admin)
        self.project_2 = Project.objects.create(name="instance2")

        self.assertEqual(Project.objects.count(), 2)
        # Get without the role in the permission
        resp = self.client.delete(
            '{}{}/'.format(url_role_model, str(self.project_1.uid)),
            HTTP_AUTHORIZATION='Token {}'.format(self.token),
        )

        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Project.objects.count(), 1)

        # Delete with the role
        self.target_model_permission.delete_roles.add(self.role_1)
        resp = self.client.delete(
            '{}{}/'.format(url_role_model, str(self.project_2.uid)),
            HTTP_AUTHORIZATION='Token {}'.format(self.token),
        )
        self.assertEqual(
            resp.status_code, status.HTTP_204_NO_CONTENT, msg=resp.content
        )
        self.assertEqual(Project.objects.count(), 0)


@override_settings(USE_CONCRETE_ROLES=True)
class CRUDTestCaseWithScope(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_user('johndoe@netsach.org')
        self.admin.set_password('plop')
        self.admin.set_level('admin')
        self.admin.save()
        self.confirmation = UserConfirmation.objects.create(user=self.admin)
        self.confirmation.confirmed = True
        self.confirmation.save()
        url = '/api/v1.1/auth/login/'
        resp = self.client.post(
            url, {"email": "johndoe@netsach.org", "password": "plop"}
        )
        self.token = resp.data['token']

        self.divider_1 = DefaultDivider.objects.create(name='Divider1')
        self.divider_2 = DefaultDivider.objects.create(name='Divider2')

        # Add one role to the user
        self.role_1 = ConcreteRole.objects.create(name="role_1")
        self.role_1.users.add(self.admin)

        # Create the permission linked to the Project
        self.target_model_permission, _ = ConcretePermission.objects.get_or_create(
            model_name="Project"
        )

        self.project_1 = Project.objects.create(
            name="instance1", defaultdivider=self.divider_1
        )
        self.project_2 = Project.objects.create(
            name="instance2", defaultdivider=self.divider_2
        )

        self.admin.defaultdividers.add(self.divider_1)

    def test_create_role_w_scope(self):
        url_role_model = '/api/v1.1/project/'

        # Post without the role in the permission
        resp = self.client.post(
            url_role_model,
            {'name': 'instance2'},
            HTTP_AUTHORIZATION='Token {}'.format(self.token),
        )

        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(resp.data['name'], 'instance2')
        self.assertEqual(Project.objects.count(), 3)

        self.target_model_permission.create_roles.add(self.role_1)

        # Post with the role
        resp = self.client.post(
            url_role_model,
            {'name': 'instance3'},
            HTTP_AUTHORIZATION='Token {}'.format(self.token),
            HTTP_X_ENTITY_UID=str(self.divider_1.uid),
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(resp.data['name'], 'instance3')
        self.assertEqual(Project.objects.count(), 4)

    def test_retrieve_role_w_scope(self):
        url_role_model = '/api/v1.1/project/'

        # Get without the role in the permission
        resp = self.client.get(
            url_role_model,
            {},
            HTTP_AUTHORIZATION='Token {}'.format(self.token),
            HTTP_X_ENTITY_UID=str(self.divider_1.uid),
        )

        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        self.target_model_permission.retrieve_roles.add(self.role_1)
        # Get with the role
        resp = self.client.get(
            url_role_model,
            {},
            HTTP_AUTHORIZATION='Token {}'.format(self.token),
            HTTP_X_ENTITY_UID=str(self.divider_1.uid),
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.data['results']), 1)

        # Get with the role

        resp = self.client.get(
            url_role_model,
            {},
            HTTP_AUTHORIZATION='Token {}'.format(self.token),
            HTTP_X_ENTITY_UID=str(self.divider_1.uid),
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.data['results']), 1)

        resp = self.client.get(
            '{}{}/'.format(url_role_model, str(self.project_1.uid)),
            HTTP_AUTHORIZATION='Token {}'.format(self.token),
            HTTP_X_ENTITY_UID=str(self.divider_1.uid),
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['name'], 'instance1')

    def test_update_role_w_scope(self):
        url_role_model = '/api/v1.1/project/'
        self.project_1.can_admin_users.add(self.admin)
        # Patch without the role in the permission
        resp = self.client.patch(
            '{}{}/'.format(url_role_model, str(self.project_1.uid)),
            {'name': 'New Instance Name'},
            HTTP_AUTHORIZATION='Token {}'.format(self.token),
            HTTP_X_ENTITY_UID=str(self.divider_1.uid),
        )

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.project_1.refresh_from_db()
        self.assertEqual(self.project_1.name, 'New Instance Name')

        # Patch with the role
        self.target_model_permission.update_roles.add(self.role_1)
        resp = self.client.patch(
            '{}{}/'.format(url_role_model, str(self.project_1.uid)),
            {'name': 'New Instance Name 2'},
            HTTP_AUTHORIZATION='Token {}'.format(self.token),
            HTTP_X_ENTITY_UID=str(self.divider_1.uid),
        )
        self.assertEqual(
            resp.status_code, status.HTTP_200_OK, msg=resp.content
        )
        self.project_1.refresh_from_db()
        self.assertEqual(self.project_1.name, 'New Instance Name 2')

    def test_delete_role_w_scope(self):
        url_role_model = '/api/v1.1/project/'
        self.project_1.can_admin_users.add(self.admin)

        # Get without the role in the permission
        resp = self.client.delete(
            '{}{}/'.format(url_role_model, str(self.project_1.uid)),
            HTTP_AUTHORIZATION='Token {}'.format(self.token),
            HTTP_X_ENTITY_UID=str(self.divider_1.uid),
        )

        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Project.objects.count(), 1)

        # Delete with the role
        self.target_model_permission.delete_roles.add(self.role_1)
        resp = self.client.delete(
            '{}{}/'.format(url_role_model, str(self.project_2.uid)),
            HTTP_AUTHORIZATION='Token {}'.format(self.token),
        )
        self.assertEqual(
            resp.status_code, status.HTTP_204_NO_CONTENT, msg=resp.content
        )
        self.assertEqual(Project.objects.count(), 0)
