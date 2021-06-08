# coding: utf-8
from rest_framework.test import APITestCase
from django.test import Client
from rest_framework import status
from concrete_datastore.concrete.models import Project
from tests.utils import create_an_user_and_get_token
from django.test import override_settings


@override_settings(DEBUG=True)
class ApiV1_1SetsTestCase(APITestCase):
    def setUp(self):
        self.user, self.token = create_an_user_and_get_token()
        self.client = Client(HTTP_AUTHORIZATION='Token {}'.format(self.token))

        self.url_projects = '/api/v1.1/project/'

        for i in range(5):
            resp = self.client.post(
                self.url_projects,
                {'name': 'Project{}'.format(i), 'archived': (i % 2 == 0)},
            )
            self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

        self.assertEqual(Project.objects.count(), 5)
        self.assertEqual(Project.objects.filter(archived=True).count(), 3)

    def test_sets_no_query(self):

        projects_set = (
            self.client.get('{}sets/'.format(self.url_projects))
            .json()
            .get('sets')
        )

        self.assertTrue('archived' in projects_set)
        self.assertEqual(projects_set['archived'], [False, True])

        self.assertTrue('name' in projects_set)
        self.assertEqual(
            set(projects_set['name']),
            set(['Project1', 'Project2', 'Project0', 'Project3', 'Project4']),
        )

    def test_sets_query_on_archived(self):
        projects_set = (
            self.client.get(
                '{}sets/?timestamp_start=0.0&archived=true'.format(
                    self.url_projects
                )
            )
            .json()
            .get('sets')
        )

        self.assertTrue('archived' in projects_set)
        self.assertEqual(projects_set['archived'], [True])

    def test_sets_on_users(self):
        users_set = (
            self.client.get(
                '/api/v1.1/user/sets/?timestamp_start=0.0&archived=true'
            )
            .json()
            .get('sets')
        )

        self.assertDictEqual(
            users_set, {'uid': [str(self.user.uid)]}
        )

    def test_sets_simple_list(self):

        projects_list = self.client.get(
            '{}?timestamp_start=0.0'.format(self.url_projects)
        )
        self.assertNotEqual(len(projects_list.json().get('results', [])), 0)
        # ts_now = time.time()
        # resp = self.client.get(
        #     '{}?timestamp_start={}'.format(url_projects, ts_now),
        # )
        # self.assertEqual(resp.status_code, status.HTTP_200_OK, msg=resp.content)
        # self.assertEqual(resp.data['deleted_uids'], [])
        # for i in range(3):
        #     Project.objects.get(name='Project{}'.format(i)).delete()
        #     self.assertEqual(resp.status_code, status.HTTP_200_OK)

        # resp = self.client.get(
        #     '{}?timestamp_start={}'.format(url_projects, ts_now)
        # )
        # self.assertEqual(
        #     len(resp.data['deleted_uids']),
        #     3
        # )
