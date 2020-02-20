# coding: utf-8
from rest_framework.test import APITestCase
from rest_framework.status import HTTP_201_CREATED, HTTP_200_OK
from concrete_datastore.concrete.models import (
    User,
    UserConfirmation,
    DefaultDivider,
)


#: Simple user does not have access to other users but can create users
class SimpleUserChangeScopesTestCase(APITestCase):
    def setUp(self):

        # Creation of a simpleuser
        self.simpleuser = User.objects.create_user('simpleuser@netsach.org')
        self.simpleuser.set_password('plop')
        self.simpleuser.set_level('simpleuser')
        self.simpleuser.save()
        # User 1 auth
        UserConfirmation.objects.create(
            user=self.simpleuser, confirmed=True
        ).save()

        url = '/api/v1/auth/login/'
        resp = self.client.post(
            url, {"email": "simpleuser@netsach.org", "password": "plop"}
        )
        self.token = resp.data['token']

        self.divider_1 = DefaultDivider.objects.create(name='Divider1')
        self.divider_2 = DefaultDivider.objects.create(name='Divider2')
        self.divider_3 = DefaultDivider.objects.create(name='Divider3')
        self.divider_4 = DefaultDivider.objects.create(name='Divider4')
        self.divider_5 = DefaultDivider.objects.create(name='Divider5')

        # Creation of a superuser
        self.superuser = User.objects.create_user('superuser@netsach.org')
        self.superuser.set_password('plop')
        self.superuser.set_level('superuser')
        self.superuser.save()

        # Creation of a manager
        self.manager = User.objects.create_user('manager@netsach.org')
        self.manager.set_password('plop')
        self.manager.set_level('manager')
        self.manager.save()

        # Creation of an admin
        self.admin = User.objects.create_user('admin@netsach.org')
        self.admin.set_password('plop')
        self.admin.set_level('admin')
        self.admin.save()

        # simpleuser has 3 dividers
        self.simpleuser.defaultdividers.add(self.divider_1)
        self.simpleuser.defaultdividers.add(self.divider_2)
        self.simpleuser.defaultdividers.add(self.divider_3)

    def test_simpleuser_create_user_with_scope(self):
        url_register = '/api/v1/auth/register/'
        # Create a simple user with scope
        self.assertEqual(User.objects.all().count(), 4)
        data = {
            "email": "simple_user_created@netsach.org",
            "password1": "plop",
            "password2": "plop",
        }
        resp = self.client.post(
            url_register,
            data=data,
            HTTP_AUTHORIZATION="Token {}".format(self.token),
            HTTP_X_ENTITY_UID=str(self.divider_1.uid),
        )
        self.assertEqual(resp.status_code, HTTP_201_CREATED)
        self.assertEqual(User.objects.all().count(), 5)
        simple_user_created = User.objects.get(
            email='simple_user_created@netsach.org'
        )
        self.assertEqual(simple_user_created.defaultdividers.count(), 0)

        # Update a simpleuser is not allowed
        data = {
            "email": "simple_user_created@netsach.org",
            "password1": "notused",
            "password2": "notused",
        }
        resp = self.client.post(
            url_register,
            data=data,
            HTTP_AUTHORIZATION="Token {}".format(self.token),
            HTTP_X_ENTITY_UID=str(self.divider_2.uid),
        )

        self.assertEqual(resp.status_code, HTTP_200_OK)
        simple_user_created.refresh_from_db()
        self.assertEqual(simple_user_created.defaultdividers.count(), 0)

        # Update a manager is forbidden, it is like creating an existing user
        data = {
            "email": "manager@netsach.org",
            "password1": "notused",
            "password2": "notused",
        }
        resp = self.client.post(
            url_register,
            data=data,
            HTTP_AUTHORIZATION="Token {}".format(self.token),
            HTTP_X_ENTITY_UID=str(self.divider_4.uid),
        )

        self.assertEqual(resp.status_code, HTTP_200_OK)
        self.manager.refresh_from_db()
        self.assertEqual(self.manager.defaultdividers.count(), 0)

        # Update an admin is forbidden, it is like creating an existing user
        data = {
            "email": "admin@netsach.org",
            "password1": "notused",
            "password2": "notused",
        }
        resp = self.client.post(
            url_register,
            data=data,
            HTTP_AUTHORIZATION="Token {}".format(self.token),
            HTTP_X_ENTITY_UID=str(self.divider_4.uid),
        )

        self.assertEqual(resp.status_code, HTTP_200_OK)
        self.admin.refresh_from_db()
        self.assertEqual(self.admin.defaultdividers.count(), 0)

        # Update a superuser is forbidden, it is like creating an existing user
        data = {
            "email": "superuser@netsach.org",
            "password1": "notused",
            "password2": "notused",
        }
        resp = self.client.post(
            url_register,
            data=data,
            HTTP_AUTHORIZATION="Token {}".format(self.token),
            HTTP_X_ENTITY_UID=str(self.divider_4.uid),
        )

        self.assertEqual(resp.status_code, HTTP_200_OK)
        self.superuser.refresh_from_db()
        self.assertEqual(self.superuser.defaultdividers.count(), 0)

    def test_simpleuser_create_user_with_scope_not_owned(self):
        # Create a user with a scope not owned will not work
        # The user will be created without scope
        url_register = '/api/v1/auth/register/'
        self.assertEqual(User.objects.all().count(), 4)
        data = {
            "email": "simple_user_created@netsach.org",
            "password1": "notused",
            "password2": "notused",
        }
        resp = self.client.post(
            url_register,
            data=data,
            HTTP_AUTHORIZATION="Token {}".format(self.token),
            HTTP_X_ENTITY_UID=str(self.divider_4.uid),
        )

        self.assertEqual(resp.status_code, HTTP_201_CREATED)
        # No user has been created
        self.assertEqual(User.objects.all().count(), 5)

    def test_simpleuser_create_user_without_scope(self):
        url_register = '/api/v1/auth/register/'
        # Create user without scope
        self.assertEqual(User.objects.all().count(), 4)
        data = {
            "email": "simple_user_created@netsach.org",
            "password1": "plop",
            "password2": "plop",
        }
        resp = self.client.post(
            url_register,
            data=data,
            HTTP_AUTHORIZATION="Token {}".format(self.token),
        )
        self.assertEqual(resp.status_code, HTTP_201_CREATED)
        self.assertEqual(User.objects.all().count(), 5)
        simple_user_created = User.objects.get(
            email='simple_user_created@netsach.org'
        )
        new_dividers = simple_user_created.defaultdividers.values_list(
            'uid', flat=True
        )
        self.assertEqual(simple_user_created.defaultdividers.count(), 0)
        self.assertEqual(set(new_dividers), set())

        # Cannot recreate an existing user
        resp = self.client.post(
            url_register,
            data=data,
            HTTP_AUTHORIZATION="Token {}".format(self.token),
        )
        self.assertEqual(resp.status_code, HTTP_200_OK)
        self.assertEqual(User.objects.all().count(), 5)
        simple_user_created = User.objects.get(
            email='simple_user_created@netsach.org'
        )
        new_dividers = simple_user_created.defaultdividers.values_list(
            'uid', flat=True
        )
        self.assertEqual(simple_user_created.defaultdividers.count(), 0)
        self.assertEqual(set(new_dividers), set())
