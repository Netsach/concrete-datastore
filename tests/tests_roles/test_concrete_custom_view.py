# coding: utf-8
from rest_framework.test import APITestCase
from rest_framework import status
from concrete_datastore.concrete.models import (
    User,
    UserConfirmation,
    ConcretePermission,
    ConcreteRole,
    Project,
)
from django.test import override_settings

"""
superusers are above roles so every operations should work
"""


@override_settings(DEBUG=True)
class CustomConcreteAPIViewTestCase(APITestCase):
    def setUp(self):
        self.superuser = User.objects.create_user(
            'johndoe@netsach.org'
            # 'John',
            # 'Doe',
        )
        self.superuser.set_password('plop')
        self.superuser.set_level('superuser')
        self.superuser.save()
        self.confirmation = UserConfirmation.objects.create(
            user=self.superuser
        )
        self.confirmation.confirmed = True
        self.confirmation.save()
        url = '/api/v1.1/auth/login/'
        resp = self.client.post(
            url, {"email": "johndoe@netsach.org", "password": "plop"}
        )
        self.token = resp.data['token']

        # Add one role to the user
        self.create_role = ConcreteRole.objects.create(name="create_role")
        self.retrieve_role = ConcreteRole.objects.create(name="retrieve_role")
        self.update_role = ConcreteRole.objects.create(name="update_role")
        self.delete_role = ConcreteRole.objects.create(name="delete_role")

        # Create the permission linked to the Project
        self.permission_create, _ = ConcretePermission.objects.get_or_create(
            model_name="Model1"
        )
        self.permission_create.create_roles.add(self.create_role)
        self.permission_retrieve, _ = ConcretePermission.objects.get_or_create(
            model_name="Model2"
        )
        self.permission_retrieve.retrieve_roles.add(self.retrieve_role)
        self.create_role.users.add(self.superuser)
        self.update_role.users.add(self.superuser)
        self.retrieve_role.users.add(self.superuser)

        self.project_1 = Project.objects.create(name="instance1")
        self.role_url = '/api/v1.1/acl/role/'
        self.permission_url = '/api/v1.1/acl/permission/'

    def test_json_response_for_list_roles(self):
        resp = self.client.get(
            self.role_url, HTTP_AUTHORIZATION='Token {}'.format(self.token)
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn('objects_count', resp.json())
        self.assertIn('next', resp.json())
        self.assertIn('previous', resp.json())
        self.assertIn('results', resp.json())
        self.assertIn('objects_count_per_page', resp.json())
        self.assertIn('num_total_pages', resp.json())
        self.assertIn('num_current_page', resp.json())
        self.assertIn('max_allowed_objects_per_page', resp.json())
        self.assertIn('model_name', resp.json())
        self.assertIn('model_verbose_name', resp.json())
        self.assertIn('list_display', resp.json())
        self.assertIn('list_filter', resp.json())
        self.assertIn('total_objects_count', resp.json())
        self.assertIn('create_url', resp.json())

    def test_json_response_for_list_permission(self):
        resp = self.client.get(
            self.permission_url,
            HTTP_AUTHORIZATION='Token {}'.format(self.token),
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn('objects_count', resp.json())
        self.assertIn('next', resp.json())
        self.assertIn('previous', resp.json())
        self.assertIn('results', resp.json())
        self.assertIn('objects_count_per_page', resp.json())
        self.assertIn('num_total_pages', resp.json())
        self.assertIn('num_current_page', resp.json())
        self.assertIn('max_allowed_objects_per_page', resp.json())
        self.assertIn('model_name', resp.json())
        self.assertIn('model_verbose_name', resp.json())
        self.assertIn('list_display', resp.json())
        self.assertIn('list_filter', resp.json())
        self.assertIn('total_objects_count', resp.json())
        self.assertIn('create_url', resp.json())

    @override_settings(API_MAX_PAGINATION_SIZE=2)
    @override_settings(API_MAX_PAGINATION_SIZE_NESTED=2)
    def test_pagination_roles(self):
        resp = self.client.get(
            self.role_url, HTTP_AUTHORIZATION='Token {}'.format(self.token)
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn('next', resp.json())
        self.assertIsNotNone(resp.json()['next'])
        self.assertEqual(resp.json()['objects_count'], 2)
        self.assertEqual(resp.json()['total_objects_count'], 4)

    @override_settings(API_MAX_PAGINATION_SIZE=1)
    @override_settings(API_MAX_PAGINATION_SIZE_NESTED=1)
    def test_pagination_permissions(self):
        resp = self.client.get(
            self.permission_url,
            HTTP_AUTHORIZATION='Token {}'.format(self.token),
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn('next', resp.json())
        self.assertIsNotNone(resp.json()['next'])
        self.assertEqual(resp.json()['objects_count'], 1)
        self.assertEqual(resp.json()['total_objects_count'], 2)

    def test_since_timestamp_roles(self):
        resp = self.client.get(
            self.role_url + 'stats/timestamp_start:0.0/',
            HTTP_AUTHORIZATION='Token {}'.format(self.token),
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn('objects_count', resp.json())
        self.assertIn('timestamp_start', resp.json())
        self.assertIn('timestamp_end', resp.json())

        timestamp_end = resp.json()['timestamp_end']
        self.assertEqual(ConcreteRole.objects.count(), 4)

        ConcreteRole.objects.create(name='ExtraRole')

        self.assertEqual(ConcreteRole.objects.count(), 5)

        resp = self.client.get(
            self.role_url + f'stats/timestamp_start:{timestamp_end}/',
            HTTP_AUTHORIZATION='Token {}'.format(self.token),
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn('objects_count', resp.json())
        self.assertIn('timestamp_start', resp.json())
        self.assertIn('timestamp_end', resp.json())
        self.assertEqual(resp.json()['objects_count'], 1)
