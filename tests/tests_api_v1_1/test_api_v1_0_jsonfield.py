# coding: utf-8
from rest_framework.test import APITestCase
from rest_framework import status
from concrete_datastore.concrete.models import User, UserConfirmation
from django.test import override_settings


@override_settings(DEBUG=True)
class JsonFieldTest(APITestCase):
    def setUp(self):
        # User A
        self.userA = User.objects.create_user('user@netsach.org')
        self.userA.set_password('userA')
        self.userA.save()
        confirmation = UserConfirmation.objects.create(
            user=self.userA, confirmed=True
        )
        confirmation.save()
        url = '/api/v1.1/auth/login/'
        resp = self.client.post(
            url, {"email": "user@netsach.org", "password": "userA"}
        )
        self.token_user = resp.data['token']

    def test_jsonfield(self):
        url_json = '/api/v1.1/json-field/'

        # Send message without auth
        resp = self.client.post(
            url_json,
            {"name": "test1", "json_field": {"toto": 1, "tata": 2}},
            HTTP_AUTHORIZATION='Token {}'.format(self.token_user),
            format='json',
        )

        self.assertEqual(
            resp.status_code, status.HTTP_201_CREATED, msg=resp.content
        )

        url1 = resp.data['url']

        resp = self.client.get(
            url1, HTTP_AUTHORIZATION='Token {}'.format(self.token_user)
        )
        self.assertEqual(type(resp.data['json_field']), dict)
