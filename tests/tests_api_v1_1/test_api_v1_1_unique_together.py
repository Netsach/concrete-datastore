# coding: utf-8
from rest_framework.test import APITestCase
from rest_framework import status
from concrete_datastore.concrete.models import (
    User,
    UserConfirmation,
    UniqueTogetherModel,
)
from django.test import override_settings


@override_settings(DEBUG=True)
class UniqueTogetherTestCase(APITestCase):
    def setUp(self):

        self.userA = User.objects.create_user('usera@netsach.org')
        self.userA.set_password('plop')
        self.userA.save()
        UserConfirmation.objects.create(user=self.userA, confirmed=True).save()
        url = '/api/v1.1/auth/login/'
        resp = self.client.post(
            url, {"email": "usera@netsach.org", "password": "plop"}
        )
        self.token_a = resp.data['token']

    def test_unique_together(self):
        url_model = "/api/v1.1/unique-together-model/"

        # Création d'un objet
        resp = self.client.post(
            url_model,
            {"name": "TOTO", "field1": "TATA"},
            HTTP_AUTHORIZATION='Token {}'.format(self.token_a),
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(UniqueTogetherModel.objects.all().count(), 1)

        # Try to create another object with the same fields unique together

        resp = self.client.post(
            url_model,
            {"name": "TOTO", "field1": "TATA"},
            HTTP_AUTHORIZATION='Token {}'.format(self.token_a),
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(UniqueTogetherModel.objects.all().count(), 1)
