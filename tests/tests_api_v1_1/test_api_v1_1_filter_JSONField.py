# coding: utf-8
from rest_framework.test import APITestCase
from rest_framework import status

from concrete_datastore.concrete.models import (
    JsonField,
    User,
    UserConfirmation,
)

from django.test import override_settings


@override_settings(API_MAX_PAGINATION_SIZE_NESTED=20)
@override_settings(API_MAX_PAGINATION_SIZE=20)
@override_settings(DEFAULT_PAGE_SIZE=20)
class TestFilterJSONField(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user('test@netsach.org')
        self.user.set_password('test')
        self.user.is_superuser = True
        self.user.save()
        UserConfirmation.objects.create(user=self.user, confirmed=True).save()
        url = '/api/v1.1/auth/login/'
        resp = self.client.post(
            url, {"email": "test@netsach.org", "password": "test"}
        )
        self.token = resp.data['token']

        self.assertEqual(JsonField.objects.count(), 0)

        self.json_data_1 = {
            "global": {
                "data": {
                    "name": "Concrete",
                    "type": "python",
                    "owner": "Netsach",
                    "value": 50,
                }
            }
        }

        self.json_data_2 = {
            "global": {
                "data": {
                    "name": "App",
                    "type": "html",
                    "owner": None,
                    "value": 10,
                }
            }
        }

        self.json_data_3 = {
            "global": {
                "data": {
                    "name": "App",
                    "type": "js",
                    "owner": None,
                    "value": 90,
                }
            }
        }

        self.json_data_4 = {
            "global": {
                "data": {
                    "name": "App_2",
                    "type": "js",
                    "owner": None,
                    "value": 30,
                }
            }
        }

        self.json_1 = JsonField.objects.create(
            json_field=self.json_data_1, name='json_data_1'
        )

        self.json_2 = JsonField.objects.create(
            json_field=self.json_data_2, name='json_data_2'
        )

        self.json_3 = JsonField.objects.create(
            json_field=self.json_data_3, name='json_data_3'
        )

        self.json_4 = JsonField.objects.create(
            json_field=self.json_data_4, name='json_data_4'
        )

        self.assertEqual(JsonField.objects.count(), 4)

    def test_base_json_request(self):
        get_url = '/api/v1.1/json-field/'

        resp = self.client.get(
            get_url, HTTP_AUTHORIZATION='Token {}'.format(self.token)
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        self.assertIn('results', resp.data)
        self.assertEqual(len(resp.data['results']), 4)

        json_result = resp.data['results']

        expected_data = {
            "global": {
                "data": {
                    "name": "Concrete",
                    "type": "python",
                    "owner": "Netsach",
                    "value": 50,
                }
            }
        }

        self.assertEqual(json_result[3]['json_field'], expected_data)

    def test_filter_JSONField_with_in(self):

        get_url = (
            '/api/v1.1/json-field/?json_field__global__data__name__in=App'
        )

        resp = self.client.get(
            get_url, HTTP_AUTHORIZATION='Token {}'.format(self.token)
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        self.assertIn('results', resp.data)

        json_result = resp.data['results']

        # only one field returned from the request (__in=App)
        self.assertEqual(len(json_result), 2)

        dict_result = json_result[0]

        # assert that the json field is correctly returned from the request
        self.assertIn('json_field', dict_result)

        self.assertEqual(self.json_data_3, dict_result['json_field'])

    def test_filter_JSONField_equals(self):

        get_url = (
            '/api/v1.1/json-field/?json_field__global__data__name=App_2'
        )

        resp = self.client.get(
            get_url, HTTP_AUTHORIZATION='Token {}'.format(self.token)
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        self.assertIn('results', resp.data)

        json_result = resp.data['results']

        print(json_result)

        # only one field returned from the request (=Concrete)
        # self.assertEqual(len(json_result), 1)

        dict_result = json_result[0]

        # assert that the json field is correctly returned from the request
        self.assertIn('json_field', dict_result)

        self.assertEqual(self.json_data_4, dict_result['json_field'])
