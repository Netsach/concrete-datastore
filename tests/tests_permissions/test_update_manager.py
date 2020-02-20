# coding: utf-8
from django.test import TestCase
from rest_framework import status
from concrete_datastore.concrete.models import (
    User,
    UserConfirmation,
    DefaultDivider,
    ScopedModel,
)
from django.test import override_settings


@override_settings(API_MAX_PAGINATION_SIZE_NESTED=10)
class UpdateAndRetrieveManagerTestCase(TestCase):
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

        #: manager with scope_1
        self.manager1, self.token1 = self.create_manager_and_token(
            "manager1@netsach.org", [self.scope_1]
        )

        self.scoped1_private = ScopedModel.objects.create(
            name="scoped1_private", public=False, defaultdivider=self.scope_1
        )
        self.scoped1_public = ScopedModel.objects.create(
            name="scoped1_public", public=True, defaultdivider=self.scope_1
        )
        self.not_scoped = ScopedModel.objects.create(
            name="not_scoped", public=True
        )
        self.scoped2 = ScopedModel.objects.create(
            name="scoped2", public=False, defaultdivider=self.scope_2
        )

    def test_update_scoped_request_private_same_scope(self):
        resp = self.client.patch(
            '/api/v1/scoped-model/{}/'.format(self.scoped1_private.uid),
            {"name": "new name"},
            content_type="application/json",
            HTTP_AUTHORIZATION='Token {}'.format(self.token1),
            HTTP_X_ENTITY_UID=str(self.scope_1.uid),
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.scoped1_private.refresh_from_db()
        self.assertEqual(self.scoped1_private.name, 'new name')

    def test_update_scoped_request_private_different_scope(self):
        resp = self.client.patch(
            '/api/v1/scoped-model/{}/'.format(self.scoped1_private.uid),
            {"name": "new name"},
            content_type="application/json",
            HTTP_AUTHORIZATION='Token {}'.format(self.token_not_scoped),
            HTTP_X_ENTITY_UID=str(self.scope_1.uid),
        )
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_unscoped_request_private_same_scope(self):
        resp = self.client.patch(
            '/api/v1/scoped-model/{}/'.format(self.scoped1_private.uid),
            {"name": "new name"},
            content_type="application/json",
            HTTP_AUTHORIZATION='Token {}'.format(self.token1),
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.scoped1_private.refresh_from_db()
        self.assertEqual(self.scoped1_private.name, 'new name')

    def test_update_unscoped_request_private_different_scope(self):
        resp = self.client.patch(
            '/api/v1/scoped-model/{}/'.format(self.scoped1_private.uid),
            {"name": "new name"},
            content_type="application/json",
            HTTP_AUTHORIZATION='Token {}'.format(self.token_not_scoped),
        )
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_unscoped_request_public_different_scope(self):
        resp = self.client.patch(
            '/api/v1/scoped-model/{}/'.format(self.scoped1_public.uid),
            {"name": "new name"},
            content_type="application/json",
            HTTP_AUTHORIZATION='Token {}'.format(self.token_not_scoped),
        )
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_retrieve_scoped_request_private_same_scope(self):
        resp = self.client.get(
            '/api/v1/scoped-model/{}/'.format(self.scoped1_private.uid),
            HTTP_AUTHORIZATION='Token {}'.format(self.token1),
            HTTP_X_ENTITY_UID=str(self.scope_1.uid),
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_retrieve_scoped_request_private_different_scope(self):
        resp = self.client.get(
            '/api/v1/scoped-model/{}/'.format(self.scoped1_private.uid),
            HTTP_AUTHORIZATION='Token {}'.format(self.token_not_scoped),
            HTTP_X_ENTITY_UID=str(self.scope_1.uid),
        )
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_retrieve_unscoped_request_private_same_scope(self):
        resp = self.client.get(
            '/api/v1/scoped-model/{}/'.format(self.scoped1_private.uid),
            HTTP_AUTHORIZATION='Token {}'.format(self.token1),
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_retrieve_unscoped_request_private_different_scope(self):
        resp = self.client.get(
            '/api/v1/scoped-model/{}/'.format(self.scoped1_private.uid),
            HTTP_AUTHORIZATION='Token {}'.format(self.token_not_scoped),
        )
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_retrieve_unscoped_request_public_different_scope(self):
        resp = self.client.get(
            '/api/v1/scoped-model/{}/'.format(self.scoped1_public.uid),
            HTTP_AUTHORIZATION='Token {}'.format(self.token_not_scoped),
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
