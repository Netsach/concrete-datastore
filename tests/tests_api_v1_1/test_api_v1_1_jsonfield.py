# coding: utf-8
from rest_framework.test import APITestCase
from rest_framework import status
from concrete_datastore.concrete.models import (
    User,
    UserConfirmation,
    JsonField,
)
from django.test import override_settings


@override_settings(DEBUG=True)
class JsonFieldTest(APITestCase):
    def setUp(self):
        # User A
        self.userA = User.objects.create_user('user@netsach.org')
        self.userA.set_password('userA')
        self.userA.set_level('superuser')
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

    def test_jsonfield_filter(self):
        url_json = '/api/v1.1/json-field/'
        json1 = JsonField.objects.create(
            json_field={
                "archived": False,
                "name": "test1",
                "item": {"name": "toto", "size": 0},
            }
        )
        json2 = JsonField.objects.create(
            json_field={
                "archived": False,
                "name": "tEsT2",
                "item": {"name": "tata", "size": 2},
                "custom_field": "tata",
            }
        )
        json3 = JsonField.objects.create(
            json_field={
                "archived": True,
                "name": "name",
                "item": {"name": "TOTO", "size": 3},
                "custom_field": "toto",
            }
        )
        resp = self.client.get(
            f'{url_json}?json_field__name__icontains=test',
            HTTP_AUTHORIZATION='Token {}'.format(self.token_user),
        )

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['objects_count'], 2)
        resp_uids = set(result['uid'] for result in resp.data['results'])
        self.assertSetEqual(resp_uids, {str(json1.uid), str(json2.uid)})

        resp = self.client.get(
            f'{url_json}?json_field__item__name=toto',
            HTTP_AUTHORIZATION='Token {}'.format(self.token_user),
        )

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['objects_count'], 1)
        self.assertEqual(resp.data['results'][0]['uid'], str(json1.uid))

        resp = self.client.get(
            f'{url_json}?json_field__item__name__icontains=to',
            HTTP_AUTHORIZATION='Token {}'.format(self.token_user),
        )

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['objects_count'], 2)
        resp_uids = set(result['uid'] for result in resp.data['results'])
        self.assertSetEqual(resp_uids, {str(json1.uid), str(json3.uid)})

        print('--------------------')
        resp = self.client.get(
            f'{url_json}?json_field__archived=False',
            HTTP_AUTHORIZATION='Token {}'.format(self.token_user),
        )
        print(JsonField.objects.filter(json_field__archived="True").count())
        print(JsonField.objects.filter(json_field__archived=True).count())
        print('--------------------')

        # self.assertEqual(resp.status_code, status.HTTP_200_OK)
        # self.assertEqual(resp.data['objects_count'], 2)
        # resp_uids = set(result['uid'] for result in resp.data['results'])
        # self.assertSetEqual(resp_uids, {str(json2.uid), str(json1.uid)})

        resp = self.client.get(
            f'{url_json}?json_field__custom_field=toto',
            HTTP_AUTHORIZATION='Token {}'.format(self.token_user),
        )

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['objects_count'], 1)
        self.assertEqual(resp.data['results'][0]['uid'], str(json3.uid))

        resp = self.client.get(
            f'{url_json}?json_field__wrong_field=test',
            HTTP_AUTHORIZATION='Token {}'.format(self.token_user),
        )

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['objects_count'], 0)
