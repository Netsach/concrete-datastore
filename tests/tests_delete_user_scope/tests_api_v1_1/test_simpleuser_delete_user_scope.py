# coding: utf-8
from rest_framework.test import APITestCase
from rest_framework.status import HTTP_403_FORBIDDEN
from concrete_datastore.concrete.models import (
    User,
    UserConfirmation,
    DefaultDivider,
)


#: SimpleUser delete scopes to other users
class SimpleUserDeleteUserScopesTestCase(APITestCase):
    def setUp(self):

        # Creation of one user of each level
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
        self.token = resp.data['token']

        self.admin = User.objects.create_user('admin@netsach.org')
        self.admin.set_password('plop')
        self.admin.set_level('admin')
        self.admin.public = True
        self.admin.save()

        self.manager = User.objects.create_user('manager@netsach.org')
        self.manager.set_password('plop')
        self.manager.set_level('manager')
        self.manager.public = True
        self.manager.save()

        self.simpleuser2 = User.objects.create_user('simpleuser2@netsach.org')
        self.simpleuser2.set_password('plop')
        self.simpleuser2.public = True

        self.simpleuser2.save()

        self.super_user_2 = User.objects.create_user(
            'super_user_2@netsach.org'
        )
        self.super_user_2.set_password('plop')
        self.super_user_2.set_level('superuser')
        self.super_user_2.public = True
        self.super_user_2.save()

        self.divider_1 = DefaultDivider.objects.create(name='Divider1')
        self.divider_2 = DefaultDivider.objects.create(name='Divider2')
        self.divider_3 = DefaultDivider.objects.create(name='Divider3')
        self.divider_4 = DefaultDivider.objects.create(name='Divider4')
        self.divider_5 = DefaultDivider.objects.create(name='Divider5')

        # simpleuser has 3 dividers
        self.simpleuser.defaultdividers.add(self.divider_1)
        self.simpleuser.defaultdividers.add(self.divider_2)
        self.simpleuser.defaultdividers.add(self.divider_3)

        self.simpleuser2.defaultdividers.add(self.divider_3)
        self.manager.defaultdividers.add(self.divider_2)
        self.admin.defaultdividers.add(self.divider_1)
        self.super_user_2.defaultdividers.add(self.divider_3)

    def test_simpleuser_remove_scopes(self):
        url_user = '/api/v1.1/user/{}/'
        # Remove scopes to a super user is not allowed
        self.assertEqual(self.super_user_2.defaultdividers.count(), 1)
        resp = self.client.delete(
            url_user.format(self.super_user_2.uid),
            HTTP_AUTHORIZATION="Token {}".format(self.token),
            HTTP_X_ENTITY_UID=str(self.divider_3.uid),
        )
        self.assertEqual(resp.status_code, HTTP_403_FORBIDDEN)
        self.assertEqual(self.super_user_2.defaultdividers.count(), 1)

        # Remove scopes to an admin
        self.assertEqual(self.admin.defaultdividers.count(), 1)
        resp = self.client.delete(
            url_user.format(self.admin.uid),
            HTTP_AUTHORIZATION="Token {}".format(self.token),
            HTTP_X_ENTITY_UID=str(self.divider_1.uid),
        )
        self.assertEqual(resp.status_code, HTTP_403_FORBIDDEN)
        self.assertEqual(self.admin.defaultdividers.count(), 1)

        # Remove scopes to a manager
        self.assertEqual(self.manager.defaultdividers.count(), 1)
        resp = self.client.delete(
            url_user.format(self.manager.uid),
            HTTP_AUTHORIZATION="Token {}".format(self.token),
            HTTP_X_ENTITY_UID=str(self.divider_2.uid),
        )
        self.assertEqual(resp.status_code, HTTP_403_FORBIDDEN)
        self.assertEqual(self.manager.defaultdividers.count(), 1)

        # Remove scopes to a simple user
        self.assertEqual(self.simpleuser2.defaultdividers.count(), 1)
        resp = self.client.delete(
            url_user.format(self.simpleuser2.uid),
            HTTP_AUTHORIZATION="Token {}".format(self.token),
            HTTP_X_ENTITY_UID=str(self.divider_3.uid),
        )
        self.assertEqual(resp.status_code, HTTP_403_FORBIDDEN)
        self.assertEqual(self.simpleuser2.defaultdividers.count(), 1)

    def test_simpleuser_block_user(self):
        url_user = '/api/v1.1/user/{}/'

        # Block a super user
        self.assertEqual(self.super_user_2.level, 'superuser')
        resp = self.client.delete(
            url_user.format(self.super_user_2.uid),
            HTTP_AUTHORIZATION="Token {}".format(self.token),
        )
        self.assertEqual(resp.status_code, HTTP_403_FORBIDDEN)
        self.super_user_2.refresh_from_db()
        self.assertEqual(self.super_user_2.level, 'superuser')

        # Block an admin
        self.assertEqual(self.admin.level, 'admin')
        resp = self.client.delete(
            url_user.format(self.admin.uid),
            HTTP_AUTHORIZATION="Token {}".format(self.token),
        )
        self.assertEqual(resp.status_code, HTTP_403_FORBIDDEN)
        self.admin.refresh_from_db()
        self.assertEqual(self.admin.level, 'admin')

        # Block a manager
        self.assertEqual(self.manager.level, 'manager')
        resp = self.client.delete(
            url_user.format(self.manager.uid),
            HTTP_AUTHORIZATION="Token {}".format(self.token),
        )
        self.assertEqual(resp.status_code, HTTP_403_FORBIDDEN)
        self.manager.refresh_from_db()
        self.assertEqual(self.manager.level, 'manager')

        # Block a simple user
        self.assertEqual(self.simpleuser2.level, 'simpleuser')
        resp = self.client.delete(
            url_user.format(self.simpleuser2.uid),
            HTTP_AUTHORIZATION="Token {}".format(self.token),
        )
        self.assertEqual(resp.status_code, HTTP_403_FORBIDDEN)
        self.simpleuser2.refresh_from_db()
        self.assertEqual(self.simpleuser2.level, 'simpleuser')
