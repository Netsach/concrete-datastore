# coding: utf-8
from rest_framework.test import APITestCase
from rest_framework import status
from concrete_datastore.concrete.models import Project
from tests.utils import create_an_user_and_get_token
from django.test import Client
import time
from django.test import override_settings


@override_settings(DEBUG=True)
class TimestampTestCase(APITestCase):
    def setUp(self):
        self.user, self.token = create_an_user_and_get_token()
        self.client = Client(HTTP_AUTHORIZATION='Token {}'.format(self.token))

    def test_timestamp_wrong_parameter(self):
        url_projects = "/api/v1/project/"
        ts_now = -1
        resp = self.client.get(
            '{}?timestamp_start={}'.format(url_projects, ts_now)
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_timestamp(self):
        url_projects = "/api/v1/project/"
        for i in range(5):
            resp = self.client.post(
                url_projects, {"name": "Project{}".format(i)}
            )
            self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

        self.assertEqual(Project.objects.count(), 5)
        ts_now = time.time()
        resp = self.client.get(
            '{}?timestamp_start={}'.format(url_projects, ts_now)
        )
        self.assertEqual(
            resp.status_code, status.HTTP_200_OK, msg=resp.content
        )
        self.assertEqual(resp.data['deleted_uids'], [])
        for i in range(3):
            Project.objects.get(name='Project{}'.format(i)).delete()
            self.assertEqual(resp.status_code, status.HTTP_200_OK)

        resp = self.client.get(
            '{}?timestamp_start={}'.format(url_projects, ts_now)
        )
        self.assertEqual(len(resp.data['deleted_uids']), 3)

    # def test_timestamp_with
