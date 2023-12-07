# coding: utf-8
from rest_framework.test import APITestCase
from rest_framework import status
from concrete_datastore.concrete.models import User, Project, UserConfirmation
import time
from django.test import override_settings


@override_settings(DEBUG=True)
class TimestampTestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user('johndoe@netsach.org')
        self.user.set_level('superuser')
        self.user.set_password('plop')
        self.user.save()
        confirmation = UserConfirmation.objects.create(user=self.user)
        confirmation.confirmed = True
        confirmation.save()
        url = '/api/v1.1/auth/login/'
        resp = self.client.post(
            url, {"email": "johndoe@netsach.org", "password": "plop"}
        )
        self.token = resp.data['token']

    def test_filter_and_incremental_loading(self):
        url_projects = "/api/v1.1/project/"

        for _ in range(5):
            resp = self.client.post(
                url_projects,
                {"name": "PROJECT_RUNNING"},
                HTTP_AUTHORIZATION='Token {}'.format(self.token),
            )
            self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

        self.assertEqual(
            Project.objects.filter(name='PROJECT_RUNNING').count(), 5
        )

        #: T0: INITIAL LOADING

        url_projects_T0 = (
            "/api/v1.1/project/?timestamp_start=0&name=PROJECT_RUNNING"
        )

        resp = self.client.get(
            url_projects_T0, HTTP_AUTHORIZATION='Token {}'.format(self.token)
        )
        self.assertEqual(
            resp.status_code, status.HTTP_200_OK, msg=resp.content
        )

        self.assertEqual(resp.data['deleted_uids'], [])
        self.assertEqual(resp.data['objects_count'], 5)
        self.assertEqual(resp.data['total_objects_count'], 5)
        T0_timestamp_end = resp.data['timestamp_end']
        time.sleep(0.5)

        #: --------------------------------------------------------------------

        #: T1 : INCREMENTAL LOADING
        #:      No modifications performed
        url_projects_T1 = (
            "/api/v1.1/project/"
            "?timestamp_start={}&name=PROJECT_RUNNING".format(T0_timestamp_end)
        )
        resp = self.client.get(
            url_projects_T1, HTTP_AUTHORIZATION='Token {}'.format(self.token)
        )
        self.assertEqual(resp.data['deleted_uids'], [])
        self.assertEqual(resp.data['objects_count'], 0)
        self.assertEqual(resp.data['total_objects_count'], 5)
        T1_timestamp_end = resp.data['timestamp_end']
        time.sleep(0.5)

        #: --------------------------------------------------------------------

        #: T2 : INCREMENTAL LOADING
        #:      Updated 1 project (RUNNING -> COMPLETED)

        p = Project.objects.filter(name='PROJECT_RUNNING').first()
        p.name = 'PROJECT_COMPLETED'
        p.save()

        url_projects_T2 = (
            "/api/v1.1/project/"
            "?timestamp_start={}&name=PROJECT_RUNNING".format(T1_timestamp_end)
        )

        resp = self.client.get(
            url_projects_T2, HTTP_AUTHORIZATION='Token {}'.format(self.token)
        )
        self.assertListEqual(resp.data['deleted_uids'], [p.uid])
        self.assertEqual(resp.data['objects_count'], 0)
        self.assertEqual(resp.data['total_objects_count'], 4)
        T2_timestamp_end = resp.data['timestamp_end']
        time.sleep(0.5)

        #: --------------------------------------------------------------------

        #: T3 : INCREMENTAL LOADING
        #:      Deleted 1 project

        p = Project.objects.filter(name='PROJECT_RUNNING').first()
        p_uid = p.uid
        p.delete()

        url_projects_T3 = (
            "/api/v1.1/project/"
            "?timestamp_start={}&name=PROJECT_RUNNING".format(T2_timestamp_end)
        )

        resp = self.client.get(
            url_projects_T3, HTTP_AUTHORIZATION='Token {}'.format(self.token)
        )
        self.assertListEqual(resp.data['deleted_uids'], [p_uid])
        self.assertEqual(resp.data['objects_count'], 0)
        self.assertEqual(resp.data['total_objects_count'], 3)
        T3_timestamp_end = resp.data['timestamp_end']
        time.sleep(0.5)

        #: --------------------------------------------------------------------

        #: T4 : INCREMENTAL LOADING
        #:      Added 1 project

        p = Project.objects.create(name='PROJECT_RUNNING')

        url_projects_T4 = (
            "/api/v1.1/project/"
            "?timestamp_start={}&name=PROJECT_RUNNING".format(T3_timestamp_end)
        )

        resp = self.client.get(
            url_projects_T4, HTTP_AUTHORIZATION='Token {}'.format(self.token)
        )
        self.assertListEqual(resp.data['deleted_uids'], [])
        self.assertEqual(resp.data['objects_count'], 1)
        self.assertEqual(resp.data['total_objects_count'], 4)
        T4_timestamp_end = resp.data['timestamp_end']
        time.sleep(0.5)

        #: --------------------------------------------------------------------

        #: T5 : INCREMENTAL LOADING
        #:      Added 1 non matching project, expected: found in deleted_uids

        p = Project.objects.create(name='PROJECT_COMPLETED')

        url_projects_T5 = (
            "/api/v1.1/project/"
            "?timestamp_start={}&name=PROJECT_RUNNING".format(T4_timestamp_end)
        )

        resp = self.client.get(
            url_projects_T5, HTTP_AUTHORIZATION='Token {}'.format(self.token)
        )
        self.assertListEqual(resp.data['deleted_uids'], [p.uid])
        self.assertEqual(resp.data['objects_count'], 0)
        self.assertEqual(resp.data['total_objects_count'], 4)
        T5_timestamp_end = resp.data['timestamp_end']
        time.sleep(0.5)

        #: --------------------------------------------------------------------

        #: T6 : INCREMENTAL LOADING
        #:      doing nothing, expected: no change

        url_projects_T6 = (
            "/api/v1.1/project/"
            "?timestamp_start={}&name=PROJECT_RUNNING".format(T5_timestamp_end)
        )

        resp = self.client.get(
            url_projects_T6, HTTP_AUTHORIZATION='Token {}'.format(self.token)
        )
        self.assertListEqual(resp.data['deleted_uids'], [])
        self.assertEqual(resp.data['objects_count'], 0)
        self.assertEqual(resp.data['total_objects_count'], 4)

    def test_filter_and_incremental_loading_for_users(self):
        url_users = "/api/v1.1/user/"

        for i in range(4):
            u = User.objects.create_user(email=f'testuser{i}@netsach.com')
            u.set_level('manager')
            u.save()
        self.assertEqual(User.objects.filter(is_staff=True).count(), 5)

        #: T0: INITIAL LOADING

        url_users_T0 = "/api/v1.1/user/?timestamp_start=0&atleast=manager"

        resp = self.client.get(
            url_users_T0, HTTP_AUTHORIZATION='Token {}'.format(self.token)
        )
        self.assertEqual(
            resp.status_code, status.HTTP_200_OK, msg=resp.content
        )

        self.assertEqual(resp.data['deleted_uids'], [])
        self.assertEqual(resp.data['total_objects_count'], 5, msg=resp.data)
        self.assertEqual(resp.data['objects_count'], 5, msg=resp.data)
        T0_timestamp_end = resp.data['timestamp_end']
        time.sleep(0.5)

        #: --------------------------------------------------------------------

        #: T1 : INCREMENTAL LOADING
        #:      No modifications performed
        url_users_T1 = (
            "/api/v1.1/user/"
            "?timestamp_start={}&atleast=manager".format(T0_timestamp_end)
        )
        resp = self.client.get(
            url_users_T1, HTTP_AUTHORIZATION='Token {}'.format(self.token)
        )
        self.assertEqual(resp.data['deleted_uids'], [])
        self.assertEqual(resp.data['objects_count'], 0)
        self.assertEqual(resp.data['total_objects_count'], 5)
        T1_timestamp_end = resp.data['timestamp_end']
        time.sleep(0.5)

        #: --------------------------------------------------------------------

        #: T2 : INCREMENTAL LOADING
        #:      Updated 1 user (manager -> simpleuser)

        u = User.objects.filter(email='testuser1@netsach.com').first()
        u.set_level('simpleuser')
        u.save()

        url_users_T2 = (
            "/api/v1.1/user/"
            "?timestamp_start={}&atleast=manager".format(T1_timestamp_end)
        )

        resp = self.client.get(
            url_users_T2, HTTP_AUTHORIZATION='Token {}'.format(self.token)
        )
        self.assertListEqual(resp.data['deleted_uids'], [u.uid])
        self.assertEqual(resp.data['objects_count'], 0)
        self.assertEqual(resp.data['total_objects_count'], 4)
        T2_timestamp_end = resp.data['timestamp_end']
        time.sleep(0.5)

        #: --------------------------------------------------------------------

        #: T3 : INCREMENTAL LOADING
        #:      Block 1 user

        u = User.objects.filter(email='testuser2@netsach.com').first()
        user_uid = u.uid
        u.set_level('blocked')
        u.save()

        url_users_T3 = (
            "/api/v1.1/user/"
            "?timestamp_start={}&atleast=manager".format(T2_timestamp_end)
        )

        resp = self.client.get(
            url_users_T3, HTTP_AUTHORIZATION='Token {}'.format(self.token)
        )
        self.assertListEqual(resp.data['deleted_uids'], [user_uid])
        self.assertEqual(resp.data['objects_count'], 0)
        self.assertEqual(resp.data['total_objects_count'], 3)
        T3_timestamp_end = resp.data['timestamp_end']
        time.sleep(0.5)

        #: --------------------------------------------------------------------

        #: T4 : INCREMENTAL LOADING
        #:      Added 1 user

        u = User.objects.create(email='test7@netsach.com')
        u.set_level('manager')
        u.save()

        url_users_T4 = (
            "/api/v1.1/user/"
            "?timestamp_start={}&atleast=manager".format(T3_timestamp_end)
        )

        resp = self.client.get(
            url_users_T4, HTTP_AUTHORIZATION='Token {}'.format(self.token)
        )
        self.assertListEqual(resp.data['deleted_uids'], [])
        self.assertEqual(resp.data['objects_count'], 1)
        self.assertEqual(resp.data['total_objects_count'], 4)
        T4_timestamp_end = resp.data['timestamp_end']
        time.sleep(0.5)

        #: --------------------------------------------------------------------

        #: T5 : INCREMENTAL LOADING
        #:      Added 1 non matching user, expected: found in deleted_uids

        u = User.objects.create(email='test8@netsach.com')

        url_users_T5 = (
            "/api/v1.1/user/"
            "?timestamp_start={}&atleast=manager".format(T4_timestamp_end)
        )

        resp = self.client.get(
            url_users_T5, HTTP_AUTHORIZATION='Token {}'.format(self.token)
        )
        self.assertListEqual(resp.data['deleted_uids'], [u.uid])
        self.assertEqual(resp.data['objects_count'], 0)
        self.assertEqual(resp.data['total_objects_count'], 4)
        T5_timestamp_end = resp.data['timestamp_end']
        time.sleep(0.5)

        #: --------------------------------------------------------------------

        #: T6 : INCREMENTAL LOADING
        #:      doing nothing, expected: no change

        url_users_T6 = (
            "/api/v1.1/user/"
            "?timestamp_start={}&atleast=manager".format(T5_timestamp_end)
        )

        resp = self.client.get(
            url_users_T6, HTTP_AUTHORIZATION='Token {}'.format(self.token)
        )
        self.assertListEqual(resp.data['deleted_uids'], [])
        self.assertEqual(resp.data['objects_count'], 0)
        self.assertEqual(resp.data['total_objects_count'], 4)
