# coding: utf-8
from rest_framework.test import APITestCase
from rest_framework import status
from concrete_datastore.concrete.models import User, DefaultDivider


#: Anonymous does not have access to other users but can create users
class AnonymousChangeScopesTestCase(APITestCase):
    def setUp(self):

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

        self.divider_1 = DefaultDivider.objects.create(name='Divider1')
        self.divider_2 = DefaultDivider.objects.create(name='Divider2')
        self.divider_3 = DefaultDivider.objects.create(name='Divider3')
        self.divider_4 = DefaultDivider.objects.create(name='Divider4')
        self.divider_5 = DefaultDivider.objects.create(name='Divider5')

    def test_anonymous_create_user_with_scope(self):
        url_register = '/api/v1/auth/register/'
        # Create a simple user with scope does not add scope
        self.assertEqual(User.objects.all().count(), 3)
        data = {
            "email": "simpleuser@netsach.org",
            "password1": "plop",
            "password2": "plop",
        }
        resp = self.client.post(
            url_register, data=data, HTTP_X_ENTITY_UID=str(self.divider_1.uid)
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.all().count(), 4)
        simpleuser = User.objects.get(email='simpleuser@netsach.org')
        self.assertEqual(simpleuser.defaultdividers.count(), 0)

        # Update a simpleuser is not allowed
        data = {
            "email": "simpleuser@netsach.org",
            "password1": "notused",
            "password2": "notused",
        }
        resp = self.client.post(
            url_register, data=data, HTTP_X_ENTITY_UID=str(self.divider_2.uid)
        )

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        simpleuser.refresh_from_db()
        self.assertEqual(simpleuser.defaultdividers.count(), 0)

        # Update a manager is forbidden, it is like creating an existing user
        data = {
            "email": "manager@netsach.org",
            "password1": "notused",
            "password2": "notused",
        }
        resp = self.client.post(
            url_register, data=data, HTTP_X_ENTITY_UID=str(self.divider_4.uid)
        )

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.manager.refresh_from_db()
        self.assertEqual(self.manager.defaultdividers.count(), 0)

        # Update an admin is forbidden, it is like creating an existing user
        data = {
            "email": "admin@netsach.org",
            "password1": "notused",
            "password2": "notused",
        }
        resp = self.client.post(
            url_register, data=data, HTTP_X_ENTITY_UID=str(self.divider_4.uid)
        )

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.admin.refresh_from_db()
        self.assertEqual(self.admin.defaultdividers.count(), 0)

        # Update a superuser is forbidden, it is like creating an existing user
        data = {
            "email": "superuser@netsach.org",
            "password1": "notused",
            "password2": "notused",
        }
        resp = self.client.post(
            url_register, data=data, HTTP_X_ENTITY_UID=str(self.divider_4.uid)
        )

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.superuser.refresh_from_db()
        self.assertEqual(self.superuser.defaultdividers.count(), 0)

    def test_anonymous_create_user_without_scope(self):
        url_register = '/api/v1/auth/register/'
        # Create user without scope
        self.assertEqual(User.objects.all().count(), 3)
        data = {
            "email": "simpleuser@netsach.org",
            "password1": "plop",
            "password2": "plop",
        }
        resp = self.client.post(url_register, data=data)
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.all().count(), 4)
        simpleuser = User.objects.get(email='simpleuser@netsach.org')
        new_dividers = simpleuser.defaultdividers.values_list('uid', flat=True)
        self.assertEqual(simpleuser.defaultdividers.count(), 0)
        self.assertEqual(set(new_dividers), set())
