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


@override_settings(DEBUG=True)
class JsonFieldFiltersTest(APITestCase):
    def setUp(self):
        # User A
        self.user = User.objects.create_user('user@netsach.org')
        self.user.set_password('user')
        self.user.set_level('superuser')
        self.user.save()
        confirmation = UserConfirmation.objects.create(
            user=self.user, confirmed=True
        )
        confirmation.save()
        url = '/api/v1.1/auth/login/'
        resp = self.client.post(
            url, {"email": "user@netsach.org", "password": "user"}
        )
        self.token_user = resp.data['token']
        self.json1 = JsonField.objects.create(
            json_field={
                "name": "test1",
                "item": {
                    "name": "toto",
                    "available": False,
                    "price": 3.99e3,
                    "size": 0,
                },
                "items_list": [1, 2, 3],
                "reference": None,
            }
        )
        self.json2 = JsonField.objects.create(
            json_field={
                "name": "tEsT2",
                "item": {
                    "name": "tata",
                    "available": False,
                    "price": 0.4,
                    "size": 2,
                },
                "custom_field": "tata",
                "items_list": [4, 2, 5],
                "reference": "12345",
            }
        )
        self.json3 = JsonField.objects.create(
            json_field={
                "name": "name",
                "item": {
                    "name": "TOTO",
                    "available": True,
                    "price": 25,
                    "size": 3,
                },
                "custom_field": "toto",
                "items_list": ['1', '2', '3'],
                "reference": None,
            }
        )
        self.url_json = '/api/v1.1/json-field/'

    def test_jsonfield_filter_string(self):
        #: String values
        resp = self.client.get(
            f'{self.url_json}?json_field__name__icontains=%22test%22',
            HTTP_AUTHORIZATION='Token {}'.format(self.token_user),
        )

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['objects_count'], 2)
        resp_uids = set(result['uid'] for result in resp.data['results'])
        self.assertSetEqual(
            resp_uids, {str(self.json1.uid), str(self.json2.uid)}
        )

        resp = self.client.get(
            f'{self.url_json}?json_field__item__name=%22toto%22',
            HTTP_AUTHORIZATION='Token {}'.format(self.token_user),
        )

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['objects_count'], 1)
        self.assertEqual(resp.data['results'][0]['uid'], str(self.json1.uid))

        resp = self.client.get(
            f'{self.url_json}?json_field__item__name__icontains=%22to%22',
            HTTP_AUTHORIZATION='Token {}'.format(self.token_user),
        )

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['objects_count'], 2)
        resp_uids = set(result['uid'] for result in resp.data['results'])
        self.assertSetEqual(
            resp_uids, {str(self.json1.uid), str(self.json3.uid)}
        )

        resp = self.client.get(
            f'{self.url_json}?json_field__custom_field=%22toto%22',
            HTTP_AUTHORIZATION='Token {}'.format(self.token_user),
        )

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['objects_count'], 1)
        self.assertEqual(resp.data['results'][0]['uid'], str(self.json3.uid))

        resp = self.client.get(
            f'{self.url_json}?json_field__items_list__1=%222%22',
            HTTP_AUTHORIZATION='Token {}'.format(self.token_user),
        )

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['objects_count'], 1)
        self.assertEqual(resp.data['results'][0]['uid'], str(self.json3.uid))

        # Raise value error if the value is a string but is not between " "
        resp = self.client.get(
            f'{self.url_json}?json_field__name=test',
            HTTP_AUTHORIZATION='Token {}'.format(self.token_user),
        )

        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_jsonfield_filter_boolean(self):
        #: Boolean values with case sensitive
        resp = self.client.get(
            f'{self.url_json}?json_field__item__available=False',
            HTTP_AUTHORIZATION='Token {}'.format(self.token_user),
        )

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['objects_count'], 2)
        resp_uids = set(result['uid'] for result in resp.data['results'])
        self.assertSetEqual(
            resp_uids, {str(self.json2.uid), str(self.json1.uid)}
        )

        resp = self.client.get(
            f'{self.url_json}?json_field__item__available=faLSe',
            HTTP_AUTHORIZATION='Token {}'.format(self.token_user),
        )

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['objects_count'], 2)
        resp_uids = set(result['uid'] for result in resp.data['results'])
        self.assertSetEqual(
            resp_uids, {str(self.json2.uid), str(self.json1.uid)}
        )

    def test_jsonfield_filter_none(self):
        #: None/Null values
        resp = self.client.get(
            f'{self.url_json}?json_field__reference=null',
            HTTP_AUTHORIZATION='Token {}'.format(self.token_user),
        )

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['objects_count'], 2)
        resp_uids = set(result['uid'] for result in resp.data['results'])
        self.assertSetEqual(
            resp_uids, {str(self.json1.uid), str(self.json3.uid)}
        )

        # same result with none
        resp = self.client.get(
            f'{self.url_json}?json_field__reference=none',
            HTTP_AUTHORIZATION='Token {}'.format(self.token_user),
        )

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['objects_count'], 2)
        resp_uids = set(result['uid'] for result in resp.data['results'])
        self.assertSetEqual(
            resp_uids, {str(self.json1.uid), str(self.json3.uid)}
        )

    def test_jsonfield_filter_int(self):
        #: Int values
        resp = self.client.get(
            f'{self.url_json}?json_field__item__size__gt=0',
            HTTP_AUTHORIZATION='Token {}'.format(self.token_user),
        )

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['objects_count'], 2)
        resp_uids = set(result['uid'] for result in resp.data['results'])
        self.assertSetEqual(
            resp_uids, {str(self.json2.uid), str(self.json3.uid)}
        )

        resp = self.client.get(
            f'{self.url_json}?json_field__items_list__1=2',
            HTTP_AUTHORIZATION='Token {}'.format(self.token_user),
        )

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['objects_count'], 2)
        resp_uids = set(result['uid'] for result in resp.data['results'])
        self.assertSetEqual(
            resp_uids, {str(self.json2.uid), str(self.json1.uid)}
        )

    def test_jsonfield_filter_float(self):
        #: Float values
        resp = self.client.get(
            f'{self.url_json}?json_field__item__price__lt=300.0',
            HTTP_AUTHORIZATION='Token {}'.format(self.token_user),
        )

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['objects_count'], 2)
        resp_uids = set(result['uid'] for result in resp.data['results'])
        self.assertSetEqual(
            resp_uids, {str(self.json2.uid), str(self.json3.uid)}
        )

    def test_jsonfield_filter_wrong_field(self):
        #: If the field does not exist, no results will be given
        resp = self.client.get(
            f'{self.url_json}?json_field__wrong_field=%22test%22',
            HTTP_AUTHORIZATION='Token {}'.format(self.token_user),
        )

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['objects_count'], 0)

        resp = self.client.get(
            f'{self.url_json}?json_field__items_list__10=1',
            HTTP_AUTHORIZATION='Token {}'.format(self.token_user),
        )

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['objects_count'], 0)

        resp = self.client.get(
            f'{self.url_json}?json_field__a__b__3__c=%22test%22',
            HTTP_AUTHORIZATION='Token {}'.format(self.token_user),
        )

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['objects_count'], 0)

    def test_jsonfield_exclude(self):
        resp = self.client.get(
            f'{self.url_json}?json_field__name__icontains!=%22test%22',
            HTTP_AUTHORIZATION='Token {}'.format(self.token_user),
        )

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['objects_count'], 1)
        self.assertEqual(resp.data['results'][0]['uid'], str(self.json3.uid))
