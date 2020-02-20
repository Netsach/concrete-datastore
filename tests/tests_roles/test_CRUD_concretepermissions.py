# coding: utf-8
from rest_framework.test import APITestCase
from rest_framework import status
from concrete_datastore.concrete.models import (
    User,
    UserConfirmation,
    ConcretePermission,
    ConcreteRole,
)
from django.test import override_settings


@override_settings(DEBUG=True)
class CRUDTestCaseConcretePermission(APITestCase):
    def setUp(self):

        # Creation of an superuser
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

        # Creation of an admin
        self.admin = User.objects.create_user('admin@netsach.org')
        self.admin.set_password('plop')
        self.admin.set_level('admin')
        self.admin.save()
        # User 1 auth
        UserConfirmation.objects.create(user=self.admin, confirmed=True).save()

        url = '/api/v1.1/auth/login/'
        resp = self.client.post(
            url, {"email": "admin@netsach.org", "password": "plop"}
        )
        self.token_admin = resp.data['token']

        # Creation of a manager
        self.manager = User.objects.create_user('manager@netsach.org')
        self.manager.set_password('plop')
        self.manager.set_level('manager')
        self.manager.save()
        # User 1 auth
        UserConfirmation.objects.create(
            user=self.manager, confirmed=True
        ).save()

        url = '/api/v1.1/auth/login/'
        resp = self.client.post(
            url, {"email": "manager@netsach.org", "password": "plop"}
        )
        self.token_manager = resp.data['token']

        # Creation of a simpleuser
        self.simpleuser = User.objects.create_user('simpleuser@netsach.org')
        self.simpleuser.set_password('plop')
        self.simpleuser.set_level('simpleuser')
        self.simpleuser.save()
        # User 1 auth
        UserConfirmation.objects.create(
            user=self.simpleuser, confirmed=True
        ).save()

        url = '/api/v1.1/auth/login/'
        resp = self.client.post(
            url, {"email": "simpleuser@netsach.org", "password": "plop"}
        )
        self.token_simpleuser = resp.data['token']

    def test_create_ConcretePermission(self):
        url_concrete_permission = '/api/v1.1/acl/permission/'

        self.assertEqual(ConcretePermission.objects.count(), 0)

        # Post with superuser
        resp = self.client.post(
            url_concrete_permission,
            {'model_name': 'Permission 1'},
            HTTP_AUTHORIZATION='Token {}'.format(self.token_superuser),
        )

        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(resp.data['model_name'], 'Permission 1')
        self.assertEqual(ConcretePermission.objects.count(), 1)

        # Post with admin
        resp = self.client.post(
            url_concrete_permission,
            {'model_name': 'Permission 2'},
            HTTP_AUTHORIZATION='Token {}'.format(self.token_admin),
        )

        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(resp.data['model_name'], 'Permission 2')
        self.assertEqual(ConcretePermission.objects.count(), 2)

        # Post with manager
        resp = self.client.post(
            url_concrete_permission,
            {'model_name': 'Permission 3'},
            HTTP_AUTHORIZATION='Token {}'.format(self.token_manager),
        )

        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(ConcretePermission.objects.count(), 2)

        # Post with simple user
        resp = self.client.post(
            url_concrete_permission,
            {'model_name': 'Permission 4'},
            HTTP_AUTHORIZATION='Token {}'.format(self.token_simpleuser),
        )

        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(ConcretePermission.objects.count(), 2)

    def test_retrieve_ConcretePermission(self):
        url_concrete_permission = '/api/v1.1/acl/permission/'

        self.permission1 = ConcretePermission.objects.create(
            model_name='Permission 1'
        )
        self.assertEqual(ConcretePermission.objects.count(), 1)

        # GET with superuser
        resp = self.client.get(
            url_concrete_permission,
            HTTP_AUTHORIZATION='Token {}'.format(self.token_superuser),
        )

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.data['results']), 1)

        resp = self.client.get(
            '{}{}/'.format(url_concrete_permission, str(self.permission1.uid)),
            HTTP_AUTHORIZATION='Token {}'.format(self.token_superuser),
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(
            resp.data['model_name'], 'Permission 1', msg=resp.content
        )

        # GET with admin
        resp = self.client.get(
            url_concrete_permission,
            HTTP_AUTHORIZATION='Token {}'.format(self.token_admin),
        )

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.data['results']), 1)

        resp = self.client.get(
            '{}{}/'.format(url_concrete_permission, str(self.permission1.uid)),
            HTTP_AUTHORIZATION='Token {}'.format(self.token_admin),
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['model_name'], 'Permission 1')

        # GET with manager
        resp = self.client.get(
            url_concrete_permission,
            HTTP_AUTHORIZATION='Token {}'.format(self.token_manager),
        )

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.data['results']), 1)

        resp = self.client.get(
            '{}{}/'.format(url_concrete_permission, str(self.permission1.uid)),
            HTTP_AUTHORIZATION='Token {}'.format(self.token_manager),
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['model_name'], 'Permission 1')

        # GET with simpleuser
        resp = self.client.get(
            url_concrete_permission,
            HTTP_AUTHORIZATION='Token {}'.format(self.token_simpleuser),
        )

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.data['results']), 1)

        resp = self.client.get(
            '{}{}/'.format(url_concrete_permission, str(self.permission1.uid)),
            HTTP_AUTHORIZATION='Token {}'.format(self.token_simpleuser),
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['model_name'], 'Permission 1')

    def test_update_ConcretePermission(self):
        url_concrete_permission = '/api/v1.1/acl/permission/'

        self.permission1 = ConcretePermission.objects.create(
            model_name='Permission 1'
        )
        self.role1 = ConcreteRole.objects.create(name='role1')
        self.role2 = ConcreteRole.objects.create(name='role2')
        self.role3 = ConcreteRole.objects.create(name='role3')
        self.role4 = ConcreteRole.objects.create(name='role4')
        self.assertEqual(ConcretePermission.objects.count(), 1)

        # PATCH with superuser
        resp = self.client.patch(
            '{}{}/'.format(url_concrete_permission, str(self.permission1.uid)),
            data={
                'model_name': 'Permission Superuser',
                'create_roles_uid': [str(self.role1.uid)],
            },
            HTTP_AUTHORIZATION='Token {}'.format(self.token_superuser),
        )

        self.assertEqual(
            resp.status_code, status.HTTP_200_OK, msg=resp.content
        )
        self.assertEqual(resp.data['model_name'], 'Permission Superuser')
        self.permission1.refresh_from_db()
        self.assertEqual(self.permission1.model_name, 'Permission Superuser')
        self.assertEqual(self.permission1.create_roles.count(), 1)

        # PATCH with admin
        resp = self.client.patch(
            '{}{}/'.format(url_concrete_permission, str(self.permission1.uid)),
            data={
                'model_name': 'Permission admin',
                'update_roles_uid': [str(self.role2.uid)],
            },
            HTTP_AUTHORIZATION='Token {}'.format(self.token_admin),
        )

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['model_name'], 'Permission admin')
        self.permission1.refresh_from_db()
        self.assertEqual(self.permission1.model_name, 'Permission admin')
        self.assertEqual(self.permission1.update_roles.count(), 1)

        # PATCH with manager
        resp = self.client.patch(
            '{}{}/'.format(url_concrete_permission, str(self.permission1.uid)),
            data={
                'model_name': 'Permission manager',
                'delete_roles_uid': [str(self.role3.uid)],
            },
            HTTP_AUTHORIZATION='Token {}'.format(self.token_manager),
        )

        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)
        self.permission1.refresh_from_db()
        self.assertEqual(self.permission1.model_name, 'Permission admin')
        self.assertEqual(self.permission1.delete_roles.count(), 0)

        # PATCH with simpleuser
        resp = self.client.patch(
            '{}{}/'.format(url_concrete_permission, str(self.permission1.uid)),
            data={
                'model_name': 'Permission simpleuser',
                'delete_roles_uid': [str(self.role3.uid)],
            },
            HTTP_AUTHORIZATION='Token {}'.format(self.token_simpleuser),
        )

        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)
        self.permission1.refresh_from_db()
        self.assertEqual(self.permission1.model_name, 'Permission admin')
        self.assertEqual(self.permission1.delete_roles.count(), 0)

    def test_delete_ConcretePermission(self):
        url_concrete_permission = '/api/v1.1/acl/permission/'

        self.permission1 = ConcretePermission.objects.create(
            model_name='Permission 1'
        )
        self.permission2 = ConcretePermission.objects.create(
            model_name='Permission 2'
        )
        self.permission3 = ConcretePermission.objects.create(
            model_name='Permission 3'
        )
        self.permission4 = ConcretePermission.objects.create(
            model_name='Permission 4'
        )
        self.assertEqual(ConcretePermission.objects.count(), 4)

        # DELETE with superuser
        resp = self.client.delete(
            '{}{}/'.format(url_concrete_permission, str(self.permission1.uid)),
            HTTP_AUTHORIZATION='Token {}'.format(self.token_superuser),
        )

        self.assertEqual(
            resp.status_code,
            status.HTTP_405_METHOD_NOT_ALLOWED,
            msg=resp.content,
        )
        self.assertEqual(ConcretePermission.objects.count(), 4)

        # DELETE with admin
        resp = self.client.delete(
            '{}{}/'.format(url_concrete_permission, str(self.permission2.uid)),
            HTTP_AUTHORIZATION='Token {}'.format(self.token_admin),
        )

        self.assertEqual(
            resp.status_code,
            status.HTTP_405_METHOD_NOT_ALLOWED,
            msg=resp.content,
        )
        self.assertEqual(ConcretePermission.objects.count(), 4)

        # DELETE with manager
        resp = self.client.delete(
            '{}{}/'.format(url_concrete_permission, str(self.permission3.uid)),
            HTTP_AUTHORIZATION='Token {}'.format(self.token_manager),
        )

        self.assertEqual(
            resp.status_code, status.HTTP_403_FORBIDDEN, msg=resp.content
        )
        self.assertEqual(ConcretePermission.objects.count(), 4)

        # DELETE with simpleuser
        resp = self.client.delete(
            '{}{}/'.format(url_concrete_permission, str(self.permission4.uid)),
            HTTP_AUTHORIZATION='Token {}'.format(self.token_simpleuser),
        )

        self.assertEqual(
            resp.status_code, status.HTTP_403_FORBIDDEN, msg=resp.content
        )
        self.assertEqual(ConcretePermission.objects.count(), 4)
