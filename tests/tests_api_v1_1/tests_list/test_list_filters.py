# coding: utf-8
from rest_framework.test import APITestCase
from django.test import Client
from tests.utils import create_an_user_and_get_token
from django.test import override_settings


@override_settings(DEBUG=True)
class ApiV1_1ListFiltersTestCase(APITestCase):
    def setUp(self):
        self.user, self.token = create_an_user_and_get_token()
        self.client = Client(HTTP_AUTHORIZATION='Token {}'.format(self.token))

    def test_sets_no_query(self):

        response = self.client.get('/api/v1.1/project/')
        list_filters = response.json()['list_filter']

        self.assertTrue('name' in list_filters)
        self.assertEqual(list_filters['name'], 'char')

        self.assertTrue('archived' in list_filters)
        self.assertEqual(list_filters['archived'], 'bool')
