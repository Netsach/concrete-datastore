# coding: utf-8
from rest_framework.test import APITestCase
from concrete_datastore.concrete.models import (
    User,
    UserConfirmation,
    DefaultDivider,
)
from rest_framework.status import (
    HTTP_201_CREATED,
    HTTP_200_OK,
    HTTP_403_FORBIDDEN,
)


#: Manager user create scopes
class ManagerChangeScopesTestCase(APITestCase):
    def setUp(self):

        # Creation of an manager
        self.manager = User.objects.create_user('manager@netsach.org')
        self.manager.set_password('plop')
        self.manager.set_level('manager')
        self.manager.save()
        # User 1 auth
        UserConfirmation.objects.create(
            user=self.manager, confirmed=True
        ).save()

        url = '/api/v1/auth/login/'
        resp = self.client.post(
            url, {"email": "manager@netsach.org", "password": "plop"}
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

        # Creation of an admin
        self.admin = User.objects.create_user('admin@netsach.org')
        self.admin.set_password('plop')
        self.admin.set_level('admin')
        self.admin.save()

        # Creation of an manager 2
        self.manager2 = User.objects.create_user('manager2@netsach.org')
        self.manager2.set_password('plop')
        self.manager2.set_level('manager2')
        self.manager2.save()

        # manager has 3 dividers
        self.manager.defaultdividers.add(self.divider_1)
        self.manager.defaultdividers.add(self.divider_2)
        self.manager.defaultdividers.add(self.divider_3)

    def test_manager_create_user_with_scope(self):
        url_register = '/api/v1/auth/register/'
        # Create a simple user with scope
        self.assertEqual(User.objects.all().count(), 4)
        data = {
            "email": "simple_user@netsach.org",
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
        simple_user = User.objects.get(email='simple_user@netsach.org')
        new_dividers = simple_user.defaultdividers.values_list(
            'uid', flat=True
        )
        self.assertEqual(simple_user.defaultdividers.count(), 1)
        self.assertEqual(set(new_dividers), set([self.divider_1.uid]))

        # Update the user with another divider
        data = {
            "email": "simple_user@netsach.org",
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
        simple_user = User.objects.get(email='simple_user@netsach.org')
        new_dividers = simple_user.defaultdividers.values_list(
            'uid', flat=True
        )
        self.assertEqual(simple_user.defaultdividers.count(), 2)
        self.assertEqual(
            set(new_dividers), set([self.divider_1.uid, self.divider_2.uid])
        )

        # Update a manager is allowed
        data = {
            "email": "manager2@netsach.org",
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
        self.manager2.refresh_from_db()
        new_dividers = self.manager2.defaultdividers.values_list(
            'uid', flat=True
        )
        self.assertEqual(self.manager2.defaultdividers.count(), 1)
        self.assertEqual(set(new_dividers), set([self.divider_2.uid]))

        # Update an admin is forbidden
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

        self.assertEqual(resp.status_code, HTTP_403_FORBIDDEN)
        self.admin.refresh_from_db()
        self.assertEqual(self.admin.defaultdividers.count(), 0)

        # Update a superuser is forbidden
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

        self.assertEqual(resp.status_code, HTTP_403_FORBIDDEN)
        self.superuser.refresh_from_db()
        self.assertEqual(self.superuser.defaultdividers.count(), 0)

    def test_manager_create_user_with_scope_not_owned(self):
        url_register = '/api/v1/auth/register/'
        self.assertEqual(User.objects.all().count(), 4)
        # Update a manager with a scope not owned is forbidden
        data = {
            "email": "manager2@netsach.org",
            "password1": "notused",
            "password2": "notused",
        }
        resp = self.client.post(
            url_register,
            data=data,
            HTTP_AUTHORIZATION="Token {}".format(self.token),
            HTTP_X_ENTITY_UID=str(self.divider_4.uid),
        )

        self.assertEqual(resp.status_code, HTTP_403_FORBIDDEN)
        self.manager2.refresh_from_db()
        new_dividers = self.manager2.defaultdividers.values_list(
            'uid', flat=True
        )
        self.assertEqual(self.manager2.defaultdividers.count(), 0)
        self.assertEqual(set(new_dividers), set())
        # Create a user with a scope not owned is forbidden
        data = {
            "email": "simple_user@netsach.org",
            "password1": "notused",
            "password2": "notused",
        }
        resp = self.client.post(
            url_register,
            data=data,
            HTTP_AUTHORIZATION="Token {}".format(self.token),
            HTTP_X_ENTITY_UID=str(self.divider_4.uid),
        )

        self.assertEqual(resp.status_code, HTTP_403_FORBIDDEN)
        # No user has been created
        self.assertEqual(User.objects.all().count(), 4)

    def test_manager_create_user_without_scope(self):
        url_register = '/api/v1/auth/register/'
        # Create user without scope
        self.assertEqual(User.objects.all().count(), 4)
        data = {
            "email": "simple_user@netsach.org",
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
        simple_user = User.objects.get(email='simple_user@netsach.org')
        new_dividers = simple_user.defaultdividers.values_list(
            'uid', flat=True
        )
        self.assertEqual(simple_user.defaultdividers.count(), 0)
        self.assertEqual(set(new_dividers), set())

        # Cannot recreate an existing user
        resp = self.client.post(
            url_register,
            data=data,
            HTTP_AUTHORIZATION="Token {}".format(self.token),
        )
        self.assertEqual(resp.status_code, HTTP_200_OK)
        self.assertEqual(User.objects.all().count(), 5)
        simple_user = User.objects.get(email='simple_user@netsach.org')
        new_dividers = simple_user.defaultdividers.values_list(
            'uid', flat=True
        )
        self.assertEqual(simple_user.defaultdividers.count(), 0)
        self.assertEqual(set(new_dividers), set())
