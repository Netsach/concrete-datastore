# coding: utf-8
from rest_framework.test import APITestCase
from rest_framework.status import HTTP_204_NO_CONTENT, HTTP_200_OK
from concrete_datastore.concrete.models import (
    User,
    UserConfirmation,
    DefaultDivider,
    Category,
    Group,
)


#: Admin user create user with scope
class TestRemoveUserScope(APITestCase):
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

        # Creation a simple user
        self.simpleuser = User.objects.create_user('simpleuser@netsach.org')
        self.simpleuser.set_password('plop')
        self.simpleuser.set_level('simpleuser')
        self.simpleuser.save()

        self.divider_1 = DefaultDivider.objects.create(name='Divider1')
        self.divider_2 = DefaultDivider.objects.create(name='Divider2')

        self.simpleuser.defaultdividers.add(self.divider_1)
        self.simpleuser.defaultdividers.add(self.divider_2)

        self.category1 = Category.objects.create(
            name='Category1', defaultdivider=self.divider_1
        )
        self.category1.can_view_users.add(self.simpleuser)

        self.category2 = Category.objects.create(
            name='Category2', defaultdivider=self.divider_1
        )
        self.category2.can_view_users.add(self.simpleuser)

        self.category3 = Category.objects.create(
            name='Category3', defaultdivider=self.divider_2
        )
        self.category3.can_view_users.add(self.simpleuser)
        # Group G1
        self.group1 = Group.objects.create(name='G1')
        self.group1.members.add(self.simpleuser)

    def test_remove_scope_patch(self):
        url_user = '/api/v1.1/user/{}/'
        self.assertEqual(self.simpleuser.viewable_categorys.count(), 3)

        # Remove divider 1
        self.assertEqual(self.simpleuser.defaultdividers.count(), 2)

        resp = self.client.patch(
            url_user.format(self.simpleuser.uid),
            data={"defaultdividers": [self.divider_2.uid]},
            HTTP_AUTHORIZATION="Token {}".format(self.token),
        )
        self.assertEqual(resp.status_code, HTTP_200_OK, msg=resp.content)
        self.assertEqual(self.simpleuser.defaultdividers.count(), 1)
        self.assertEqual(self.category2.can_view_users.count(), 0)
        self.assertEqual(self.simpleuser.viewable_categorys.count(), 1)

    def test_remove_scope_delete_user(self):
        url_user = '/api/v1.1/user/{}/'
        self.assertEqual(self.simpleuser.viewable_categorys.count(), 3)

        # Remove divider 1
        self.assertEqual(self.simpleuser.defaultdividers.count(), 2)

        resp = self.client.delete(
            url_user.format(self.simpleuser.uid),
            HTTP_X_ENTITY_UID=str(self.divider_1.uid),
            HTTP_AUTHORIZATION="Token {}".format(self.token),
        )
        self.assertEqual(resp.status_code, HTTP_200_OK, msg=resp.content)
        self.assertEqual(self.simpleuser.defaultdividers.count(), 1)
        self.assertEqual(self.category2.can_view_users.count(), 0)
        self.assertEqual(self.simpleuser.viewable_categorys.count(), 1)

    def test_remove_scope_block_user_delete(self):
        # When a user is blocked, the dividers are removed
        # The user is also removed from group members
        url_user = '/api/v1.1/user/{}/'
        self.assertEqual(self.simpleuser.viewable_categorys.count(), 3)

        # Remove divider 1
        self.assertEqual(self.simpleuser.defaultdividers.count(), 2)

        resp = self.client.delete(
            url_user.format(self.simpleuser.uid),
            HTTP_AUTHORIZATION="Token {}".format(self.token),
        )
        self.assertEqual(
            resp.status_code, HTTP_204_NO_CONTENT, msg=resp.content
        )
        self.assertEqual(self.simpleuser.defaultdividers.count(), 0)
        self.assertEqual(self.category2.can_view_users.count(), 0)
        self.assertEqual(self.simpleuser.viewable_categorys.count(), 0)

    def test_remove_scope_block_user_patch(self):
        # When a user is blocked, the dividers are removed
        # The user is also removed from group members

        url_user = '/api/v1.1/user/{}/'
        self.assertEqual(self.simpleuser.viewable_categorys.count(), 3)

        # Remove divider 1
        self.assertEqual(self.simpleuser.defaultdividers.count(), 2)

        resp = self.client.patch(
            url_user.format(self.simpleuser.uid),
            data={'level': 'blocked'},
            HTTP_AUTHORIZATION="Token {}".format(self.token),
        )
        self.assertEqual(resp.status_code, HTTP_200_OK, msg=resp.content)
        self.assertEqual(self.simpleuser.defaultdividers.count(), 0)
        self.assertEqual(self.category2.can_view_users.count(), 0)
        self.assertEqual(self.simpleuser.viewable_categorys.count(), 0)
        self.assertEqual(self.group1.members.count(), 0)
