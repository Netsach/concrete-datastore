# coding: utf-8
from rest_framework.test import APITestCase
from rest_framework.status import HTTP_201_CREATED, HTTP_200_OK
from concrete_datastore.concrete.models import (
    User,
    UserConfirmation,
    DefaultDivider,
)


#: Admin user create user with scope
class SuperUserCreateUserScopesTestCase(APITestCase):
    def setUp(self):

        # Creation a super user
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
        self.token = resp.data['token']

        self.divider_1 = DefaultDivider.objects.create(name='Divider1')
        self.divider_2 = DefaultDivider.objects.create(name='Divider2')
        self.divider_3 = DefaultDivider.objects.create(name='Divider3')
        self.divider_4 = DefaultDivider.objects.create(name='Divider4')
        self.divider_5 = DefaultDivider.objects.create(name='Divider5')

        # Superuser has 3 dividers
        self.superuser.defaultdividers.add(self.divider_1)
        self.superuser.defaultdividers.add(self.divider_2)
        self.superuser.defaultdividers.add(self.divider_3)

    def test_su_create_user_with_scope(self):
        url_register = '/api/v1.1/auth/register/'
        # Add scopes to a superuser
        self.assertEqual(User.objects.all().count(), 1)
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
        self.assertEqual(User.objects.all().count(), 2)
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

        # Update the user with a divider su does not have
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

        self.assertEqual(resp.status_code, HTTP_200_OK)
        simple_user = User.objects.get(email='simple_user@netsach.org')
        new_dividers = simple_user.defaultdividers.values_list(
            'uid', flat=True
        )
        self.assertEqual(simple_user.defaultdividers.count(), 3)
        self.assertEqual(
            set(new_dividers),
            set([self.divider_1.uid, self.divider_2.uid, self.divider_4.uid]),
        )

    def test_su_create_user_without_scope(self):
        url_register = '/api/v1.1/auth/register/'
        # Create user without scope
        self.assertEqual(User.objects.all().count(), 1)
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
        self.assertEqual(User.objects.all().count(), 2)
        simple_user = User.objects.get(email='simple_user@netsach.org')
        new_dividers = simple_user.defaultdividers.values_list(
            'uid', flat=True
        )
        self.assertEqual(simple_user.defaultdividers.count(), 0)
        self.assertEqual(set(new_dividers), set())

        resp = self.client.post(
            url_register,
            data=data,
            HTTP_AUTHORIZATION="Token {}".format(self.token),
        )
        self.assertEqual(resp.status_code, HTTP_200_OK)
        self.assertEqual(User.objects.all().count(), 2)
        simple_user = User.objects.get(email='simple_user@netsach.org')
        new_dividers = simple_user.defaultdividers.values_list(
            'uid', flat=True
        )
        self.assertEqual(simple_user.defaultdividers.count(), 0)
        self.assertEqual(set(new_dividers), set())
