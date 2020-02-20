# coding: utf-8
from rest_framework.test import APITestCase
from rest_framework import status

from concrete_datastore.concrete.models import User, UserConfirmation, Project
from django.conf import settings
from django.test import override_settings


@override_settings(DEBUG=True)
class TestPaginatedViews(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            'johndoe@netsach.org',
            # 'John',
            # 'Doe',
        )
        self.user.set_password('plop')
        self.user.is_superuser = True
        self.user.save()
        # User 1 auth
        UserConfirmation.objects.create(user=self.user, confirmed=True).save()
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
        for i in range(20):
            Project.objects.create(name="project_name_{}".format(i))
        self.objects_count = Project.objects.count()

    def test_page_size(self):
        pagination = 'not_int'
        get_url = '/api/v1/project/?c_resp_page_size={}'.format(pagination)
        resp = self.client.get(
            get_url, HTTP_AUTHORIZATION='Token {}'.format(self.token)
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

        pagination = 0
        get_url = '/api/v1/project/?c_resp_page_size={}'.format(pagination)
        resp = self.client.get(
            get_url, HTTP_AUTHORIZATION='Token {}'.format(self.token)
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

        pagination = 5
        get_url = '/api/v1/project/?c_resp_page_size={}'.format(pagination)
        resp = self.client.get(
            get_url, HTTP_AUTHORIZATION='Token {}'.format(self.token)
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(
            resp.data['objects_count_per_page'],
            min(settings.API_MAX_PAGINATION_SIZE, pagination),
        )
        self.assertEqual(
            resp.data['max_allowed_objects_per_page'],
            settings.API_MAX_PAGINATION_SIZE,
        )
        self.assertEqual(
            resp.data["objects_count"],
            min(
                pagination,
                self.objects_count,
                settings.API_MAX_PAGINATION_SIZE,
            ),
        )

    @override_settings(API_MAX_PAGINATION_SIZE=10)
    def test_nested(self):
        nested = 'abc'
        get_url = '/api/v1/project/?c_resp_nested={}'.format(nested)
        resp = self.client.get(
            get_url, HTTP_AUTHORIZATION='Token {}'.format(self.token)
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

        nested = 'false'
        get_url = '/api/v1/project/?c_resp_nested={}'.format(nested)
        resp = self.client.get(
            get_url, HTTP_AUTHORIZATION='Token {}'.format(self.token)
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        self.assertIn('objects_count', resp.data)
        self.assertIn('next', resp.data)
        self.assertIn('previous', resp.data)
        self.assertIn('results', resp.data)
        self.assertIn('objects_count_per_page', resp.data)
        self.assertIn('num_total_pages', resp.data)
        self.assertIn('num_current_page', resp.data)

        self.assertEqual(
            resp.data['objects_count'],
            min(self.objects_count, settings.API_MAX_PAGINATION_SIZE),
        )

        get_url = '/api/v1/project/?c_resp_page_size=7&c_resp_nested=false'
        resp = self.client.get(
            get_url, HTTP_AUTHORIZATION='Token {}'.format(self.token)
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(
            resp.data["objects_count"],
            min(7, self.objects_count, settings.API_MAX_PAGINATION_SIZE),
        )

    def test_nested_paginated_filtered(self):
        pagination = 7
        get_url = (
            '/api/v1/project/?c_resp_page_size={}'
            '&c_resp_nested=true&name=project_name_1'.format(pagination)
        )
        resp = self.client.get(
            get_url, HTTP_AUTHORIZATION='Token {}'.format(self.token)
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(Project.objects.count(), 20)
        self.assertEqual(resp.data['objects_count'], 1)
        self.assertEqual(
            resp.data['objects_count_per_page'],
            min(
                pagination,
                settings.API_MAX_PAGINATION_SIZE,
                settings.API_MAX_PAGINATION_SIZE_NESTED,
            ),
        )
