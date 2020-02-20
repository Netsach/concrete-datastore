# coding: utf-8
from rest_framework.test import APITestCase
from rest_framework import status
from concrete_datastore.concrete.models import User, UserConfirmation, Crud
from django.test import override_settings
import pendulum


REST_FRAMEWORK = {
    'DATETIME_FORMAT': "%Y-%m-%dT%H:%M:%SZ",
    'COERCE_DECIMAL_TO_STRING': False,
    'PAGE_SIZE': 5,
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework.authentication.BasicAuthentication',
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.TokenAuthentication',
    ),
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.LimitOffsetPagination',
    'DEFAULT_RENDERER_CLASSES': (
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
    ),
}


@override_settings(DEBUG=True)
class TimestampTestCase(APITestCase):
    def setUp(self):
        '''
        Generate  2 times the API_MAX_PAGINATION_SIZE. The purpose of this series
        of tests is to assert that the pagination is working with the timestamp
         parameter and the filter is effective for modified objects
        For these tests, API_MAX_PAGINATION_SIZE is set to 5.
        '''

        for i in range(0, 12):
            Crud.objects.create(name='object_{i}'.format(i=i))

        self.user = User.objects.create_user(
            'johndoe@netsach.org'
            # 'John',
            # 'Doe',
        )
        self.user.set_password('plop')
        self.user.save()
        self.confirmation = UserConfirmation.objects.create(user=self.user)
        self.confirmation.confirmed = True
        self.confirmation.save()
        url = '/api/v1/auth/login/'
        resp = self.client.post(
            url,
            {
                # "username": 'johndoe@netsach.org',
                "email": "johndoe@netsach.org",
                "password": "plop",
            },
        )
        self.token = resp.data['token']
        self.user.set_level('superuser')
        self.user.save()

    @override_settings(
        API_MAX_PAGINATION_SIZE=5, REST_FRAMEWORK=REST_FRAMEWORK
    )
    def test_pagination(self):
        from django.conf import settings

        self.assertEqual(settings.API_MAX_PAGINATION_SIZE, 5)
        self.assertEqual(settings.REST_FRAMEWORK['PAGE_SIZE'], 5)
        url_crud = '/api/v1/crud/?c_resp_nested=false'
        resp = self.client.get(
            url_crud, {}, HTTP_AUTHORIZATION='Token {}'.format(self.token)
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["objects_count"], 5)
        self.assertEqual(resp.data["objects_count_per_page"], 5)
        self.assertEqual(resp.data["num_total_pages"], 3)
        self.assertEqual(resp.data["num_current_page"], 1)

    @override_settings(
        API_MAX_PAGINATION_SIZE=5, REST_FRAMEWORK=REST_FRAMEWORK
    )
    def test_pagination_2(self):
        url_crud = "/api/v1/crud/?c_resp_nested=false&c_resp_page_size=6"
        resp = self.client.get(
            url_crud, {}, HTTP_AUTHORIZATION='Token {}'.format(self.token)
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK, resp)
        self.assertEqual(resp.data["objects_count_per_page"], 5)
        self.assertEqual(resp.data["num_total_pages"], 3)
        self.assertEqual(resp.data["num_current_page"], 1)
        self.assertEqual(resp.data["objects_count"], 5)

    def test_since_timestamp(self):
        url_timestamp_0 = "/api/v1/crud/?c_resp_nested=false&timestamp_start=0"
        url_timestamp_X = "/api/v1/crud/?c_resp_nested=false&timestamp_start="
        resp = self.client.get(
            url_timestamp_0,
            {},
            HTTP_AUTHORIZATION='Token {}'.format(self.token),
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK, resp)

        timestamp = pendulum.now('utc').timestamp()

        object_x = resp.data['results'][0]
        resp = self.client.patch(
            object_x['url'],
            data={'name': "MODIFIED"},
            HTTP_AUTHORIZATION='Token {}'.format(self.token),
        )
        self.assertEqual(resp.status_code, 200)
        resp = self.client.get(
            url_timestamp_X + str(timestamp),
            HTTP_AUTHORIZATION='Token {}'.format(self.token),
        )

        results = resp.data['results']
        self.assertEqual(len(results), 1)

    @override_settings(
        API_MAX_PAGINATION_SIZE=5, REST_FRAMEWORK=REST_FRAMEWORK
    )
    def test_nested_pagination(self):
        from django.conf import settings

        self.assertEqual(settings.API_MAX_PAGINATION_SIZE, 5)
        self.assertEqual(settings.REST_FRAMEWORK['PAGE_SIZE'], 5)
        url_crud = '/api/v1/crud/?c_resp_nested=true'
        resp = self.client.get(
            url_crud, {}, HTTP_AUTHORIZATION='Token {}'.format(self.token)
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["objects_count"], 5)
        self.assertEqual(resp.data["objects_count_per_page"], 5)
        self.assertEqual(resp.data["num_total_pages"], 3)
        self.assertEqual(resp.data["num_current_page"], 1)

    @override_settings(
        API_MAX_PAGINATION_SIZE=5, REST_FRAMEWORK=REST_FRAMEWORK
    )
    def test_nested_pagination_2(self):
        url_crud = "/api/v1/crud/?c_resp_nested=true&c_resp_page_size=6"
        resp = self.client.get(
            url_crud, {}, HTTP_AUTHORIZATION='Token {}'.format(self.token)
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK, resp)
        self.assertEqual(resp.data["objects_count_per_page"], 5)
        self.assertEqual(resp.data["num_total_pages"], 3)
        self.assertEqual(resp.data["num_current_page"], 1)
        self.assertEqual(resp.data["objects_count"], 5)

    @override_settings(
        API_MAX_PAGINATION_SIZE=5, REST_FRAMEWORK=REST_FRAMEWORK
    )
    def test_nested_since_timestamp(self):
        url_timestamp_0 = "/api/v1/crud/?c_resp_nested=true&timestamp_start=0"
        url_timestamp_X = "/api/v1/crud/?c_resp_nested=true&timestamp_start="
        resp = self.client.get(
            url_timestamp_0,
            {},
            HTTP_AUTHORIZATION='Token {}'.format(self.token),
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK, resp)

        timestamp = pendulum.now('utc').timestamp()

        object_x = resp.data['results'][0]
        resp = self.client.patch(
            object_x['url'],
            data={'name': "MODIFIED"},
            HTTP_AUTHORIZATION='Token {}'.format(self.token),
        )
        self.assertEqual(resp.status_code, 200)
        resp = self.client.get(
            url_timestamp_X + str(timestamp),
            HTTP_AUTHORIZATION='Token {}'.format(self.token),
        )

        results = resp.data['results']
        self.assertEqual(len(results), 1)
