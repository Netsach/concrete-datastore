# coding: utf-8
from rest_framework.test import APITestCase
from rest_framework import status
from concrete_datastore.concrete.models import (
    User,
    ScopedModel,
    NotScopedModel,
    DefaultDivider,
    UserConfirmation,
)
from django.test import override_settings


@override_settings(DEBUG=True)
class UnscopedRequestPermissionsTestCase(APITestCase):
    def create_custom_user(self, level, suffixe='', scopes=None):
        if scopes is None:
            scopes = []
        username = '{}_{}'.format(level, suffixe) if suffixe else level
        email = '{}@netsach.org'.format(username)

        user = User.objects.create_user(email)
        user.set_password('plop')
        user.set_level(level)

        for scope in scopes:
            user.defaultdividers.add(scope)
        user.save()

        confirmation = UserConfirmation.objects.create(user=user)
        confirmation.confirmed = True
        confirmation.save()

        url = '/api/v1.1/auth/login/'
        resp = self.client.post(url, {"email": email, "password": "plop"})

        return user, resp.data['token']

    def setUp(self):

        self.scope_1 = DefaultDivider.objects.create(name="Scope 1")
        self.scope_2 = DefaultDivider.objects.create(name="Scope 2")

        self.superuser, self.token_superuser = self.create_custom_user(
            level='superuser'
        )

        self.manager_scoped1, self.token_manager_scoped1 = self.create_custom_user(
            level='manager', suffixe='scoped1', scopes=[self.scope_1]
        )
        self.manager_scoped2, self.token_manager_scoped2 = self.create_custom_user(
            level='manager', suffixe='scoped2', scopes=[self.scope_2]
        )
        self.manager_not_scoped, self.token_manager_not_scoped = self.create_custom_user(
            level='manager', suffixe='not_scoped'
        )
        self.manager_scoped_all, self.token_manager_scoped_all = self.create_custom_user(
            level='manager',
            suffixe='scoped_all',
            scopes=[self.scope_1, self.scope_2],
        )
        self.admin_scoped1, self.token_admin_scoped1 = self.create_custom_user(
            level='admin', suffixe='scoped1', scopes=[self.scope_1]
        )
        self.admin_scoped2, self.token_admin_scoped2 = self.create_custom_user(
            level='admin', suffixe='scoped2', scopes=[self.scope_2]
        )
        self.simpleuser, self.token_simpleuser = self.create_custom_user(
            level='simpleuser'
        )

        self.scoped1 = ScopedModel.objects.create(
            name="scoped1", defaultdivider=self.scope_1, public=False
        )
        self.scoped1.can_view_users.set(
            [self.manager_scoped2, self.simpleuser]
        )
        self.scoped2 = ScopedModel.objects.create(
            name="scoped2", defaultdivider=self.scope_2, public=False
        )
        self.scoped2.can_admin_users.set(
            [self.simpleuser, self.manager_not_scoped]
        )

        self.not_scoped = NotScopedModel.objects.create(
            name="not_scoped", public=False
        )

        self.not_scoped_public = NotScopedModel.objects.create(
            name="not_scoped_public", public=True
        )

    def test_public(self):
        resp = self.client.get(
            '/api/v1.1/not-scoped-model/',
            HTTP_AUTHORIZATION='Token {}'.format(self.token_simpleuser),
        )

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertTrue('results' in resp.data)
        results_index_by_uid = [
            result['uid'] for result in resp.data['results']
        ]
        self.assertEqual(len(results_index_by_uid), 1)
        self.assertTrue(
            str(self.not_scoped_public.uid) in results_index_by_uid
        )
        self.assertFalse(str(self.not_scoped.uid) in results_index_by_uid)

    def test_public_scoped(self):
        scoped1_public = ScopedModel.objects.create(
            name="scoped1_public", public=True, defaultdivider=self.scope_1
        )
        resp = self.client.get(
            '/api/v1.1/scoped-model/',
            HTTP_AUTHORIZATION='Token {}'.format(self.token_simpleuser),
        )

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertTrue('results' in resp.data)
        results_index_by_uid = [
            result['uid'] for result in resp.data['results']
        ]
        self.assertTrue(str(self.scoped1.uid) in results_index_by_uid)
        self.assertTrue(str(scoped1_public.uid) in results_index_by_uid)

    def test_can_admin_users(self):
        #:  get list
        resp = self.client.get(
            '/api/v1.1/scoped-model/',
            HTTP_AUTHORIZATION='Token {}'.format(self.token_simpleuser),
        )
        self.assertEqual(self.simpleuser.defaultdividers.count(), 0)

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertTrue('results' in resp.data)

        results_index_by_uid = [
            result['uid'] for result in resp.data['results']
        ]
        self.assertTrue(str(self.scoped1.pk) in results_index_by_uid)
        self.assertTrue(str(self.scoped2.pk) in results_index_by_uid)

        resp = self.client.get(
            '/api/v1.1/scoped-model/',
            HTTP_AUTHORIZATION='Token {}'.format(
                self.token_manager_not_scoped
            ),
        )
        results_index_by_uid = [
            result['uid'] for result in resp.data['results']
        ]
        self.assertTrue(str(self.scoped2.pk) in results_index_by_uid)
        self.assertFalse(str(self.scoped1.pk) in results_index_by_uid)

        #:  update
        url = '/api/v1.1/scoped-model/'

        resp = self.client.patch(
            '{}{}/'.format(url, self.scoped2.uid),
            data={"name": "Updated Name"},
            HTTP_AUTHORIZATION='Token {}'.format(self.token_simpleuser),
        )
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

        resp = self.client.patch(
            '{}{}/'.format(url, self.scoped2.uid),
            data={"name": "New Name"},
            HTTP_AUTHORIZATION='Token {}'.format(
                self.token_manager_not_scoped
            ),
        )
        self.assertEqual(
            resp.status_code, status.HTTP_200_OK, msg=resp.content
        )
        self.scoped2.refresh_from_db()
        self.assertEqual(self.scoped2.name, "New Name")

    def test_list_permissions_by_level_scoped_model(self):

        url = '/api/v1.1/scoped-model/'

        #: Users that can see the instance scoped_1 with list
        for token in [
            self.token_superuser,
            self.token_admin_scoped1,
            self.token_admin_scoped2,
            self.token_manager_scoped1,
            self.token_manager_scoped_all,
            self.token_manager_scoped2,  #: can_admin_user
            self.token_simpleuser,  #: can_view_users
        ]:
            resp = self.client.get(
                url, {}, HTTP_AUTHORIZATION='Token {}'.format(token)
            )
            results_index_by_uid = [
                result['uid'] for result in resp.data['results']
            ]
            self.assertEqual(resp.status_code, status.HTTP_200_OK)
            self.assertTrue(str(self.scoped1.pk) in results_index_by_uid)

        #: Users that can't see the instance scoped_1 with list
        resp = self.client.get(
            url,
            {},
            HTTP_AUTHORIZATION='Token {}'.format(
                self.token_manager_not_scoped
            ),
        )
        results_index_by_uid = [
            result['uid'] for result in resp.data['results']
        ]
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertFalse(str(self.scoped1.pk) in results_index_by_uid)

        #: Users that can see the instance scoped_2 with list
        for token in [
            self.token_superuser,
            self.token_admin_scoped2,
            self.token_admin_scoped1,
            self.token_manager_scoped_all,
            self.token_manager_scoped2,
            self.token_manager_not_scoped,
            self.token_simpleuser,
        ]:
            resp = self.client.get(
                url, {}, HTTP_AUTHORIZATION='Token {}'.format(token)
            )
            results_index_by_uid = [
                result['uid'] for result in resp.data['results']
            ]
            self.assertEqual(resp.status_code, status.HTTP_200_OK)
            self.assertTrue(str(self.scoped2.pk) in results_index_by_uid)

        #: Users that can't see the instance scoped_2 with list
        resp = self.client.get(
            url,
            {},
            HTTP_AUTHORIZATION='Token {}'.format(self.token_manager_scoped1),
        )
        results_index_by_uid = [
            result['uid'] for result in resp.data['results']
        ]
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertFalse(str(self.scoped2.pk) in results_index_by_uid)

    def test_delete_permissions_by_level_scoped_model(self):

        url = '/api/v1.1/scoped-model/'

        self.assertEqual(ScopedModel.objects.count(), 2)

        for token in [
            self.token_admin_scoped1,
            self.token_admin_scoped2,
            self.token_manager_scoped1,
            self.token_manager_scoped2,
            self.token_manager_scoped_all,
            self.token_manager_not_scoped,
            self.token_simpleuser,
        ]:
            resp = self.client.delete(
                '{}{}/'.format(url, self.scoped1.uid),
                {},
                HTTP_AUTHORIZATION='Token {}'.format(token),
            )
            self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(ScopedModel.objects.count(), 2)

        resp = self.client.delete(
            '{}{}/'.format(url, self.scoped1.uid),
            HTTP_AUTHORIZATION='Token {}'.format(self.token_superuser),
        )
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(ScopedModel.objects.count(), 1)

    def test_can_view_users_no_admin_rigths(self):
        """
        ** This test FAILS **
        ---------------------
        This describes the wanted behaviour for `can_view_users`.
        In this case, the manager_scoped2 can see the instance scoped1
        because he is in the can_view_users of scoped1, but can't retrieve
        the instance.
        """

        name_before_update = self.scoped1.name
        resp = self.client.get(
            '/api/v1.1/scoped-model/',
            HTTP_AUTHORIZATION='Token {}'.format(self.token_manager_scoped2),
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        result_uids = [result['uid'] for result in resp.data['results']]
        self.assertIn(
            str(self.scoped1.uid),
            result_uids,
            msg="{} --> {}".format(self.scoped1.uid, result_uids),
        )
        resp = self.client.get(
            '/api/v1.1/scoped-model/{}/'.format(self.scoped1.uid),
            HTTP_AUTHORIZATION='Token {}'.format(self.token_manager_scoped2),
        )
        self.assertEqual(
            resp.status_code, status.HTTP_200_OK, msg=resp.content
        )

        resp = self.client.patch(
            '/api/v1.1/scoped-model/{}/'.format(self.scoped1.uid),
            data={"name": "Updated Name"},
            HTTP_AUTHORIZATION='Token {}'.format(self.token_manager_scoped2),
        )
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)
        self.scoped1.refresh_from_db()
        self.assertEqual(self.scoped1.name, name_before_update)

    def test_update_permissions_by_level_scoped_model(self):
        url = '/api/v1.1/scoped-model/'

        resp = self.client.patch(
            '{}{}/'.format(url, self.scoped1.uid),
            data={"name": "Updated Name"},
            HTTP_AUTHORIZATION='Token {}'.format(self.token_simpleuser),
        )
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)
        resp = self.client.patch(
            '{}{}/'.format(url, self.scoped1.uid),
            data={"name": "Updated Name"},
            HTTP_AUTHORIZATION='Token {}'.format(
                self.token_manager_not_scoped
            ),
        )
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

        resp = self.client.patch(
            '{}{}/'.format(url, self.scoped1.uid),
            data={"name": "Updated Name v1"},
            HTTP_AUTHORIZATION='Token {}'.format(self.token_manager_scoped1),
        )
        self.assertEqual(
            resp.status_code, status.HTTP_200_OK, msg=resp.content
        )
        self.scoped1.refresh_from_db()
        self.assertEqual(self.scoped1.name, "Updated Name v1")

        resp = self.client.patch(
            '{}{}/'.format(url, self.scoped1.uid),
            data={"name": "Updated Name v2"},
            HTTP_AUTHORIZATION='Token {}'.format(self.token_admin_scoped1),
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.scoped1.refresh_from_db()
        self.assertEqual(self.scoped1.name, "Updated Name v2")

        resp = self.client.patch(
            '{}{}/'.format(url, self.scoped1.uid),
            data={"name": "Updated Name v3"},
            HTTP_AUTHORIZATION='Token {}'.format(self.token_superuser),
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.scoped1.refresh_from_db()
        self.assertEqual(self.scoped1.name, "Updated Name v3")

        resp = self.client.patch(
            '{}{}/'.format(url, self.scoped1.uid),
            data={"name": "Updated Name v4"},
            HTTP_AUTHORIZATION='Token {}'.format(self.token_admin_scoped2),
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.scoped1.refresh_from_db()
        self.assertEqual(self.scoped1.name, "Updated Name v4")

    def test_create_permissions_with_user_level(self):
        url = '/api/v1.1/scoped-model/'
        self.assertEqual(ScopedModel.objects.count(), 2)

        data1 = {"name": "scoped3", "public": False}
        for token in [
            self.token_simpleuser,
            self.token_manager_scoped1,
            self.token_manager_scoped_all,
            self.token_manager_not_scoped,
        ]:
            resp = self.client.post(
                url,
                data=data1,
                HTTP_AUTHORIZATION="Token {}".format(token),
                HTTP_X_ENTITY_UID=str(self.scope_1.uid),
            )
            self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

        resp = self.client.post(
            url,
            data=data1,
            HTTP_AUTHORIZATION="Token {}".format(self.token_superuser),
            HTTP_X_ENTITY_UID=str(self.scope_1.uid),
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(ScopedModel.objects.count(), 3)

        data2 = {"name": "scoped4", "public": False}
        resp = self.client.post(
            url,
            data=data2,
            HTTP_AUTHORIZATION="Token {}".format(self.token_admin_scoped1),
            HTTP_X_ENTITY_UID=str(self.scope_1.uid),
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(ScopedModel.objects.count(), 4)

        data3 = {"name": "scoped5", "public": False}
        resp = self.client.post(
            url,
            data=data3,
            HTTP_AUTHORIZATION="Token {}".format(self.token_admin_scoped2),
            HTTP_X_ENTITY_UID=str(self.scope_1.uid),
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(ScopedModel.objects.count(), 5)
