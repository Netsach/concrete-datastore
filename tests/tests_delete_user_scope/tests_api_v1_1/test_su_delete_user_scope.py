# coding: utf-8
from rest_framework.test import APITestCase
from rest_framework.status import HTTP_204_NO_CONTENT, HTTP_200_OK
from concrete_datastore.concrete.models import (
    User,
    UserConfirmation,
    DefaultDivider,
)


#: Superuser delete scopes to other users
class SuperUserDeleteUserScopesTestCase(APITestCase):
    def setUp(self):

        # Creation of one user of each level
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

        self.admin = User.objects.create_user('admin@netsach.org')
        self.admin.set_password('plop')
        self.admin.set_level('admin')

        self.manager = User.objects.create_user('manager@netsach.org')
        self.manager.set_password('plop')
        self.manager.set_level('manager')
        self.manager.save()

        self.simple_user = User.objects.create_user('simpleuser@netsach.org')
        self.simple_user.set_password('plop')
        self.simple_user.save()

        self.super_user_2 = User.objects.create_user(
            'super_user_2@netsach.org'
        )
        self.super_user_2.set_password('plop')
        self.super_user_2.set_level('superuser')
        self.super_user_2.save()
        # User 1 auth
        UserConfirmation.objects.create(
            user=self.super_user_2, confirmed=True
        ).save()

        self.divider_1 = DefaultDivider.objects.create(name='Divider1')
        self.divider_2 = DefaultDivider.objects.create(name='Divider2')
        self.divider_3 = DefaultDivider.objects.create(name='Divider3')
        self.divider_4 = DefaultDivider.objects.create(name='Divider4')
        self.divider_5 = DefaultDivider.objects.create(name='Divider5')

        # Superuser has 3 dividers
        self.superuser.defaultdividers.add(self.divider_1)
        self.superuser.defaultdividers.add(self.divider_2)
        self.superuser.defaultdividers.add(self.divider_3)

        # Superuser has 3 dividers
        self.simple_user.defaultdividers.add(self.divider_3)
        self.manager.defaultdividers.add(self.divider_2)
        self.admin.defaultdividers.add(self.divider_1)
        self.super_user_2.defaultdividers.add(self.divider_3)

    def test_su_remove_scopes(self):
        url_user = '/api/v1.1/user/{}/'
        # Remove scopes to a superuser
        self.assertEqual(self.super_user_2.defaultdividers.count(), 1)
        resp = self.client.delete(
            url_user.format(self.super_user_2.uid),
            HTTP_AUTHORIZATION="Token {}".format(self.token),
            HTTP_X_ENTITY_UID=str(self.divider_3.uid),
        )
        self.assertEqual(resp.status_code, HTTP_200_OK)
        self.assertEqual(self.super_user_2.defaultdividers.count(), 0)

        # Remove scopes to an admin
        self.assertEqual(self.admin.defaultdividers.count(), 1)
        resp = self.client.delete(
            url_user.format(self.admin.uid),
            HTTP_AUTHORIZATION="Token {}".format(self.token),
            HTTP_X_ENTITY_UID=str(self.divider_1.uid),
        )
        self.assertEqual(resp.status_code, HTTP_200_OK)
        self.assertEqual(self.admin.defaultdividers.count(), 0)

        # Remove scopes to a manager
        self.assertEqual(self.manager.defaultdividers.count(), 1)
        resp = self.client.delete(
            url_user.format(self.manager.uid),
            HTTP_AUTHORIZATION="Token {}".format(self.token),
            HTTP_X_ENTITY_UID=str(self.divider_2.uid),
        )
        self.assertEqual(resp.status_code, HTTP_200_OK)
        self.assertEqual(self.manager.defaultdividers.count(), 0)

        # Remove scopes to a simple user
        self.assertEqual(self.simple_user.defaultdividers.count(), 1)
        resp = self.client.delete(
            url_user.format(self.simple_user.uid),
            HTTP_AUTHORIZATION="Token {}".format(self.token),
            HTTP_X_ENTITY_UID=str(self.divider_3.uid),
        )
        self.assertEqual(resp.status_code, HTTP_200_OK)
        self.assertEqual(self.simple_user.defaultdividers.count(), 0)

    def test_su_block_user(self):
        url_user = '/api/v1.1/user/{}/'

        # Block a superuser
        self.assertEqual(self.super_user_2.level, 'superuser')
        resp = self.client.delete(
            url_user.format(self.super_user_2.uid),
            HTTP_AUTHORIZATION="Token {}".format(self.token),
        )
        self.assertEqual(resp.status_code, HTTP_204_NO_CONTENT)
        self.super_user_2.refresh_from_db()
        self.assertEqual(self.super_user_2.level, 'blocked')

        # Block an admin
        self.assertEqual(self.admin.level, 'admin')
        resp = self.client.delete(
            url_user.format(self.admin.uid),
            HTTP_AUTHORIZATION="Token {}".format(self.token),
        )
        self.assertEqual(resp.status_code, HTTP_204_NO_CONTENT)
        self.admin.refresh_from_db()
        self.assertEqual(self.admin.level, 'blocked')

        # Block a manager
        self.assertEqual(self.manager.level, 'manager')
        resp = self.client.delete(
            url_user.format(self.manager.uid),
            HTTP_AUTHORIZATION="Token {}".format(self.token),
        )
        self.assertEqual(resp.status_code, HTTP_204_NO_CONTENT)
        self.manager.refresh_from_db()
        self.assertEqual(self.manager.level, 'blocked')

        # Block a simple user
        self.assertEqual(self.simple_user.level, 'simpleuser')
        resp = self.client.delete(
            url_user.format(self.simple_user.uid),
            HTTP_AUTHORIZATION="Token {}".format(self.token),
        )
        self.assertEqual(resp.status_code, HTTP_204_NO_CONTENT)
        self.simple_user.refresh_from_db()
        self.assertEqual(self.simple_user.level, 'blocked')
