# coding: utf-8
from rest_framework.test import APITestCase
from rest_framework import status
from concrete_datastore.concrete.models import User, UserConfirmation
from concrete_datastore.concrete.models import (
    TestDataLeak as ModelTestDataLeak,
)
from concrete_datastore.concrete.models import DefaultDivider as DefaultScope
from django.test import override_settings


@override_settings(DEBUG=True)
class CloisonnementTestCase(APITestCase):
    def setUp(self):
        self.userA = User.objects.create_user('usera@netsach.org')
        self.userA.set_password('plop')
        self.userA.set_level('manager')
        self.userA.save()
        confirmation = UserConfirmation.objects.create(user=self.userA)
        confirmation.confirmed = True
        confirmation.save()

        url = '/api/v1.1/auth/login/'
        resp = self.client.post(
            url, {"email": "usera@netsach.org", "password": "plop"}
        )
        self.token_a = resp.data['token']

        # USER NON ADMIN
        self.userB = User.objects.create_user('userb@netsach.org')
        self.userB.set_password('plop')
        self.userB.set_level('manager')
        self.userB.save()
        confirmation = UserConfirmation.objects.create(user=self.userB)
        confirmation.confirmed = True
        confirmation.save()
        url = '/api/v1.1/auth/login/'
        resp = self.client.post(
            url, {"email": "userb@netsach.org", "password": "plop"}
        )
        self.token_b = resp.data['token']

        self.scope_1 = DefaultScope.objects.create(name="Scope 1")
        self.scope_2 = DefaultScope.objects.create(name="Scope 2")

        self.userA.defaultdividers.add(self.scope_1)
        self.userA.save()

        self.userB.defaultdividers.add(self.scope_2)
        self.userB.save()

        self.data1 = ModelTestDataLeak.objects.create(
            value="data scope 1", defaultdivider=self.scope_1, public=False
        )
        self.data2 = ModelTestDataLeak.objects.create(
            value="data scope 2", defaultdivider=self.scope_2, public=False
        )

    def test_retrieve_compliance(self):
        url = '/api/v1.1/test-data-leak/'

        # user a shall only retrieve data from scope 1
        resp = self.client.get(
            url, {}, HTTP_AUTHORIZATION='Token {}'.format(self.token_a)
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(
            resp.data["objects_count"], 1, 'Data leaks between scopes...'
        )

        # user b shall only retrieve data from scope 2
        resp = self.client.get(
            url, {}, HTTP_AUTHORIZATION='Token {}'.format(self.token_b)
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(
            resp.data["objects_count"], 1, 'Data leaks between scopes...'
        )
