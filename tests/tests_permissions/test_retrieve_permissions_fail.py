# coding: utf-8
from django.test import TestCase
from rest_framework import status
from concrete_datastore.concrete.models import (
    User,
    UserConfirmation,
    Group,
    DefaultDivider,
    ScopedModel,
)
from django.test import override_settings


@override_settings(API_MAX_PAGINATION_SIZE_NESTED=10)
class RetrievePermissionLevelTestCase(TestCase):
    def create_manager_and_token(self, email, scopes):
        manager = User.objects.create_user(email)
        manager.set_password('plop')
        manager.set_level("manager")
        for scope in scopes:
            manager.defaultdividers.add(scope)
        manager.save()

        confirmation = UserConfirmation.objects.create(user=manager)
        confirmation.confirmed = True
        confirmation.save()

        url = '/api/v1.1/auth/login/'
        resp = self.client.post(url, {"email": email, "password": "plop"})
        token = resp.data["token"]
        return manager, token

    def setUp(self):
        self.scope_1 = DefaultDivider.objects.create(name="Scope 1")
        self.scope_2 = DefaultDivider.objects.create(name="Scope 2")

        #: manager not scoped
        self.manager_not_scoped, self.token_not_scoped = self.create_manager_and_token(
            "manager_not_scoped@netsach.org", []
        )

        #: manager 1
        self.manager1, self.token1 = self.create_manager_and_token(
            "manager1@netsach.org", [self.scope_1, self.scope_2]
        )
        #: manager 2
        self.manager2, self.token2 = self.create_manager_and_token(
            "manager2@netsach.org", [self.scope_1, self.scope_2]
        )
        #: manager 3
        self.manager3, self.token3 = self.create_manager_and_token(
            "manager3@netsach.org", [self.scope_1, self.scope_2]
        )
        #: manager 4
        self.manager4, self.token4 = self.create_manager_and_token(
            "manager4@netsach.org", [self.scope_1, self.scope_2]
        )

        self.group_admin = Group.objects.create(name="Admin Group")
        self.group_admin.members.set([self.manager3])

        self.group_view = Group.objects.create(name="View Group")
        self.group_view.members.set([self.manager4])

        self.scoped1 = ScopedModel.objects.create(
            name="scoped1", public=False, defaultdivider=self.scope_1
        )

        self.not_scoped_private = ScopedModel.objects.create(
            name="not_scoped_private", public=False
        )
        self.not_scoped_public = ScopedModel.objects.create(
            name="not_scoped_public", public=True
        )
        self.scoped_public = ScopedModel.objects.create(
            name="scoped_public", defaultdivider=self.scope_1, public=True
        )
        self.scoped2_1 = ScopedModel.objects.create(
            name="scoped2_1", defaultdivider=self.scope_2, public=False
        )
        self.scoped2_1.can_view_users.set([self.manager1])
        self.scoped2_2 = ScopedModel.objects.create(
            name="scoped2_2", defaultdivider=self.scope_2, public=False
        )
        self.scoped2_2.can_admin_users.set([self.manager2])
        self.scoped2_3 = ScopedModel.objects.create(
            name="scoped2_3", defaultdivider=self.scope_2, public=False
        )
        self.scoped2_3.can_admin_groups.set([self.group_admin])
        self.scoped2_4 = ScopedModel.objects.create(
            name="scoped2_4", defaultdivider=self.scope_2, public=False
        )
        self.scoped2_4.can_view_groups.set([self.group_view])


class RetrievePermissionLevelScopedRequestTestCase(
    RetrievePermissionLevelTestCase
):
    def test_list(self):
        self.assertEqual(
            ScopedModel.objects.filter(defaultdivider=self.scope_2).count(), 4
        )
        self.assertEqual(
            ScopedModel.objects.filter(defaultdivider=self.scope_1).count(), 2
        )
        url = '/api/v1/scoped-model/'

        #: user 1
        resp = self.client.get(
            url,
            HTTP_AUTHORIZATION='Token {}'.format(self.token1),
            HTTP_X_ENTITY_UID=str(self.scope_2.uid),
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn("results", resp.data)
        self.assertEqual(len(resp.data['results']), 4)
        result_uids = [result["uid"] for result in resp.data['results']]

        self.assertIn(str(self.scoped2_1.uid), result_uids)

        resp = self.client.patch(
            "{}{}/".format(url, str(self.scoped1.uid)),
            {"name": "New Name"},
            content_type="application/json",
            HTTP_AUTHORIZATION='Token {}'.format(self.token1),
            HTTP_X_ENTITY_UID=str(self.scope_1.uid),
        )
        self.assertEqual(
            resp.status_code, status.HTTP_200_OK, msg=resp.content
        )

        resp = self.client.get(
            "{}{}/".format(url, str(self.scoped1.uid)),
            HTTP_AUTHORIZATION='Token {}'.format(self.token1),
            HTTP_X_ENTITY_UID=str(self.scope_1.uid),
        )
        self.assertEqual(
            resp.status_code, status.HTTP_200_OK, msg=resp.content
        )

        resp = self.client.get(
            "{}{}/".format(url, str(self.scoped2_1.uid)),
            HTTP_AUTHORIZATION='Token {}'.format(self.token1),
            HTTP_X_ENTITY_UID=str(self.scope_2.uid),
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        #: user 2
        resp = self.client.get(
            url,
            HTTP_AUTHORIZATION='Token {}'.format(self.token2),
            HTTP_X_ENTITY_UID=str(self.scope_2.uid),
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn("results", resp.data)
        self.assertEqual(len(resp.data['results']), 4)
        result_uids = [result["uid"] for result in resp.data['results']]

        self.assertIn(str(self.scoped2_2.uid), result_uids)

        resp = self.client.get(
            "{}{}/".format(url, self.scoped2_2.uid),
            HTTP_AUTHORIZATION='Token {}'.format(self.token2),
            HTTP_X_ENTITY_UID=str(self.scope_2.uid),
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        #: user 3
        resp = self.client.get(
            url,
            HTTP_AUTHORIZATION='Token {}'.format(self.token3),
            HTTP_X_ENTITY_UID=str(self.scope_2.uid),
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn("results", resp.data)
        self.assertEqual(len(resp.data['results']), 4)
        result_uids = [result["uid"] for result in resp.data['results']]

        self.assertIn(str(self.scoped2_3.uid), result_uids)

        resp = self.client.get(
            "{}{}/".format(url, self.scoped2_3.uid),
            HTTP_AUTHORIZATION='Token {}'.format(self.token3),
            HTTP_X_ENTITY_UID=str(self.scope_2.uid),
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        #: user 4
        resp = self.client.get(
            url,
            HTTP_AUTHORIZATION='Token {}'.format(self.token4),
            HTTP_X_ENTITY_UID=str(self.scope_2.uid),
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn("results", resp.data)
        self.assertEqual(len(resp.data['results']), 4)
        result_uids = [result["uid"] for result in resp.data['results']]

        self.assertIn(str(self.scoped2_4.uid), result_uids)

        resp = self.client.get(
            "{}{}/".format(url, self.scoped2_4.uid),
            HTTP_AUTHORIZATION='Token {}'.format(self.token4),
            HTTP_X_ENTITY_UID=str(self.scope_2.uid),
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_scoped_public(self):
        url = '/api/v1/scoped-model/'
        resp = self.client.get(
            url,
            HTTP_AUTHORIZATION='Token {}'.format(self.token1),
            HTTP_X_ENTITY_UID=str(self.scope_1.uid),
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn("results", resp.data)
        results_index_by_uid = [
            result['uid'] for result in resp.data['results']
        ]
        self.assertIn(str(self.scoped_public.uid), results_index_by_uid)

        resp = self.client.get(
            "{}{}/".format(url, self.scoped_public.uid),
            HTTP_AUTHORIZATION='Token {}'.format(self.token1),
            HTTP_X_ENTITY_UID=str(self.scope_1.uid),
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)


class RetrievePermissionLevelUnScopedRequestTestCase(
    RetrievePermissionLevelTestCase
):
    def test_list(self):
        self.assertEqual(
            ScopedModel.objects.filter(defaultdivider=self.scope_2).count(), 4
        )
        self.assertEqual(
            ScopedModel.objects.filter(defaultdivider=self.scope_1).count(), 2
        )
        url = '/api/v1/scoped-model/'

        #: user 1
        resp = self.client.get(
            url, HTTP_AUTHORIZATION='Token {}'.format(self.token1)
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn("results", resp.data)
        self.assertEqual(len(resp.data['results']), 7, msg=resp.content)
        result_uids = [result["uid"] for result in resp.data['results']]

        self.assertIn(str(self.scoped2_1.uid), result_uids)

        resp = self.client.get(
            "{}{}/".format(url, self.scoped2_1.uid),
            HTTP_AUTHORIZATION='Token {}'.format(self.token1),
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        #: user 2
        resp = self.client.get(
            url, HTTP_AUTHORIZATION='Token {}'.format(self.token2)
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn("results", resp.data)
        self.assertEqual(len(resp.data['results']), 7, msg=resp.content)
        result_uids = [result["uid"] for result in resp.data['results']]

        self.assertIn(str(self.scoped2_2.uid), result_uids)

        resp = self.client.get(
            "{}{}/".format(url, self.scoped2_2.uid),
            HTTP_AUTHORIZATION='Token {}'.format(self.token2),
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        #: user 3
        resp = self.client.get(
            url, HTTP_AUTHORIZATION='Token {}'.format(self.token3)
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn("results", resp.data)
        self.assertEqual(len(resp.data['results']), 7, msg=resp.content)
        result_uids = [result["uid"] for result in resp.data['results']]

        self.assertIn(str(self.scoped2_3.uid), result_uids)

        resp = self.client.get(
            "{}{}/".format(url, self.scoped2_3.uid),
            HTTP_AUTHORIZATION='Token {}'.format(self.token3),
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        #: user 4
        resp = self.client.get(
            url, HTTP_AUTHORIZATION='Token {}'.format(self.token4)
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn("results", resp.data)
        self.assertEqual(len(resp.data['results']), 7, msg=resp.content)
        result_uids = [result["uid"] for result in resp.data['results']]

        self.assertIn(str(self.scoped2_4.uid), result_uids)

        resp = self.client.get(
            "{}{}/".format(url, self.scoped2_4.uid),
            HTTP_AUTHORIZATION='Token {}'.format(self.token4),
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_scoped_public(self):
        url = '/api/v1/scoped-model/'
        resp = self.client.get(
            url, HTTP_AUTHORIZATION='Token {}'.format(self.token1)
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn("results", resp.data)
        results_index_by_uid = [
            result['uid'] for result in resp.data['results']
        ]
        self.assertIn(str(self.scoped_public.uid), results_index_by_uid)

        resp = self.client.get(
            "{}{}/".format(url, self.scoped_public.uid),
            HTTP_AUTHORIZATION='Token {}'.format(self.token1),
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
