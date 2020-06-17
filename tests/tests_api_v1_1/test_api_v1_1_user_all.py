# coding: utf-8
from rest_framework.test import APITestCase
from rest_framework import status
from concrete_datastore.concrete.models import User, UserConfirmation
from django.conf import settings
from django.test import override_settings


@override_settings(DEBUG=True)
class UserAllTestCase(APITestCase):
    def setUp(self):
        for i in range(10):
            self.user = User.objects.create_user(
                'johndoe{}@netsach.org'.format(i)
            )
            self.user.set_password('plop{}'.format(i))
            self.user.is_staff = True
            self.user.save()
            UserConfirmation.objects.create(
                user=self.user, confirmed=True
            ).save()
        url = '/api/v1.1/auth/login/'
        resp = self.client.post(
            url,
            {
                # "username": 'johndoe@netsach.org',
                "email": "johndoe5@netsach.org",
                "password": "plop5",
            },
        )
        self.token = resp.data['token']

    def test_get_all_user(self):
        url = '/api/v1.1/user/'
        resp = self.client.get(
            url, HTTP_AUTHORIZATION='Token {}'.format(self.token)
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_create_user(self):
        url = '/api/v1.1/user/'
        resp = self.client.post(
            url,
            {'username': 'blob'},
            HTTP_AUTHORIZATION='Token {}'.format(self.token),
        )
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_list_user(self):
        # PAGINATED RESPONSE
        url_projects = '/api/v1.1/user/'
        resp = self.client.get(
            url_projects, {}, HTTP_AUTHORIZATION='Token {}'.format(self.token)
        )
        # print(resp.data)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn("objects_count", resp.data)
        self.assertIn("next", resp.data)
        self.assertIn("previous", resp.data)
        self.assertIn("results", resp.data)
        self.assertIn("objects_count_per_page", resp.data)
        self.assertIn("num_total_pages", resp.data)
        self.assertIn("num_current_page", resp.data)

        self.assertGreater(100, settings.REST_FRAMEWORK["PAGE_SIZE"])

        self.assertEqual(
            resp.data["objects_count"], settings.API_MAX_PAGINATION_SIZE_NESTED
        )
        self.assertEqual(
            resp.data["objects_count_per_page"],
            settings.API_MAX_PAGINATION_SIZE_NESTED,
        )
        # self.assertEqual(resp.data["num_total_pages"], 1)
        self.assertEqual(resp.data["num_current_page"], 1)

        # NOT PAGINATED RESPONSE
        url_projects = '/api/v1.1/user/'
        resp = self.client.get(
            url_projects, {}, HTTP_AUTHORIZATION='Token {}'.format(self.token)
        )
        # print(resp.data)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn("objects_count", resp.data)
        self.assertIn("next", resp.data)
        self.assertIn("previous", resp.data)
        self.assertIn("results", resp.data)
        self.assertIn("objects_count_per_page", resp.data)
        self.assertIn("num_total_pages", resp.data)
        self.assertIn("num_current_page", resp.data)

        self.assertGreater(100, settings.REST_FRAMEWORK["PAGE_SIZE"])

        self.assertEqual(
            resp.data["objects_count"], settings.API_MAX_PAGINATION_SIZE_NESTED
        )
        self.assertEqual(
            resp.data["objects_count_per_page"],
            settings.API_MAX_PAGINATION_SIZE_NESTED,
        )
        self.assertEqual(resp.data["num_total_pages"], 2)
        self.assertEqual(resp.data["num_current_page"], 1)
