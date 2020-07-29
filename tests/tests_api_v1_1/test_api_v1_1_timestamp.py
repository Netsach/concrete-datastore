# coding: utf-8
from rest_framework.test import APITestCase
from rest_framework import status
from concrete_datastore.concrete.models import User, UserConfirmation, Project
import time
from django.test import override_settings


@override_settings(DEBUG=True)
class TimestampTestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            'johndoe@netsach.org'
            # 'John',
            # 'Doe',
        )
        self.user.is_superuser = True
        self.user.set_password('plop')
        self.user.save()
        self.confirmation = UserConfirmation.objects.create(user=self.user)
        self.confirmation.confirmed = True
        self.confirmation.save()
        url = '/api/v1.1/auth/login/'
        resp = self.client.post(
            url,
            {
                # "username": 'johndoe@netsach.org',
                "email": "johndoe@netsach.org",
                "password": "plop",
            },
        )
        self.token = resp.data['token']

    def test_timestamp_wrong_parameter(self):
        url_projects = "/api/v1.1/project/"
        ts_now = -1
        resp = self.client.get(
            '{}?timestamp_start={}'.format(url_projects, ts_now),
            HTTP_AUTHORIZATION='Token {}'.format(self.token),
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_timestamp(self):
        url_projects = "/api/v1.1/project/"
        for i in range(5):
            resp = self.client.post(
                url_projects,
                {"name": "Project{}".format(i)},
                HTTP_AUTHORIZATION='Token {}'.format(self.token),
            )
            self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Project.objects.count(), 5)
        ts_now = time.time()
        resp = self.client.get(
            '{}?timestamp_start={}'.format(url_projects, ts_now),
            HTTP_AUTHORIZATION='Token {}'.format(self.token),
        )
        self.assertEqual(
            resp.status_code, status.HTTP_200_OK, msg=resp.content
        )
        self.assertEqual(resp.data['deleted_uids'], [])
        for i in range(3):
            Project.objects.get(name='Project{}'.format(i)).delete()
            self.assertEqual(resp.status_code, status.HTTP_200_OK)

        resp = self.client.get(
            '{}?timestamp_start={}'.format(url_projects, ts_now),
            HTTP_AUTHORIZATION='Token {}'.format(self.token),
        )
        self.assertEqual(len(resp.data['deleted_uids']), 3)

    def test_timestamp_end_none(self):
        url_projects = "/api/v1.1/project/"
        resp = self.client.get(
            '{}?timestamp_end=None'.format(url_projects),
            HTTP_AUTHORIZATION='Token {}'.format(self.token),
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_creation_date_between_timestamps_with_filters(self):
        url_projects = "/api/v1.1/project/"
        for i in range(5):
            resp = self.client.post(
                url_projects,
                {"name": "Project{}".format(i)},
                HTTP_AUTHORIZATION='Token {}'.format(self.token),
            )
            self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Project.objects.filter(archived=False).count(), 5)
        #:  Fetch all projects with archived = False, with timestamp = 0.0
        resp = self.client.get(
            f'{url_projects}?timestamp_start=0.0&archived=false',
            HTTP_AUTHORIZATION='Token {}'.format(self.token),
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn('deleted_uids', resp.data)
        self.assertIn('results', resp.data)
        self.assertIn('timestamp_end', resp.data)
        self.assertIn('objects_count', resp.data)
        self.assertEqual(resp.data['objects_count'], 5)

        ts_end = resp.data['timestamp_end']

        #:  Store results in a local_store variable
        local_store = [obj['uid'] for obj in resp.data['results']]

        #:  Create a new project
        resp = self.client.post(
            url_projects,
            {"name": "Project5"},
            HTTP_AUTHORIZATION='Token {}'.format(self.token),
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertIn('uid', resp.data)
        self.assertEqual(Project.objects.filter(archived=False).count(), 6)

        #:  Store this new project in the local_store
        new_uid = resp.data['uid']
        local_store.append(new_uid)

        #:  Patch this new project with archived=True
        resp = self.client.patch(
            f'{url_projects}{new_uid}/',
            data={'archived': True},
            HTTP_AUTHORIZATION='Token {}'.format(self.token),
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(Project.objects.filter(archived=False).count(), 5)

        #:  Fetch all projects with archived = False, with timestamp = ts_end
        resp = self.client.get(
            f'{url_projects}?timestamp_start={ts_end}&archived=false',
            HTTP_AUTHORIZATION='Token {}'.format(self.token),
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn('deleted_uids', resp.data)
        self.assertIn('results', resp.data)
        self.assertIn('timestamp_end', resp.data)
        self.assertIn('objects_count', resp.data)

        #:  No new objects
        self.assertEqual(resp.data['objects_count'], 0)

        #:  No deleted uids for now
        self.assertEqual(len(resp.data['deleted_uids']), 1)
        for uid in map(lambda x: str(x), resp.data['deleted_uids']):
            if uid in local_store:
                local_store.remove(uid)

        #:  fetch all instances without timestamp_start
        resp = self.client.get(
            f'{url_projects}?archived=false',
            HTTP_AUTHORIZATION='Token {}'.format(self.token),
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn('results', resp.data)
        self.assertIn('objects_count', resp.data)
        self.assertEqual(resp.data['objects_count'], 5)

        #:  Get all uids in the results
        non_archived_uids = [obj['uid'] for obj in resp.data['results']]

        #:  Compare the local_store and the results form the api
        self.assertListEqual(non_archived_uids, local_store)
