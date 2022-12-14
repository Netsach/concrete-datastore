# coding: utf-8
from rest_framework.test import APITestCase
from rest_framework import status
from concrete_datastore.concrete.models import (
    User,
    UserConfirmation,
    Group,
    Village,
)
import logging
from django.test import override_settings
from django.db import connection
from django.db import reset_queries
import time

logger = logging.getLogger('concrete-datastore')


@override_settings(DEBUG=True)
class PermissionTestCase(APITestCase):
    def setUp(self):
        # User A
        # self.divider = DefaultDivider.objects.create(name='divider')

        self.admin = User.objects.create_user(
            email='admin@netsach.org', password='admin'
        )

        self.confirmation = UserConfirmation.objects.create(user=self.admin)
        self.confirmation.confirmed = True
        self.admin.set_level('admin', commit=True)
        self.confirmation.save()
        url = '/api/v1/auth/login/'
        resp = self.client.post(
            url, {"email": "admin@netsach.org", "password": "admin"}
        )
        self.admin_token = resp.data['token']

        self.group_can_admin = Group.objects.create(
            name="Group for administration"
        )
        self.group_can_admin.members.set([self.admin.uid])

        self.url = '/api/v1.1/village/'

    def test_retrieve_permission_for_simple(self):
        village1 = Village.objects.create(name='v1')
        village1.can_admin_groups.set([self.group_can_admin.uid])
        village1.can_admin_groups.set([self.group_can_admin.uid])
        reset_queries()

        # Get beginning stats
        start_queries = len(connection.queries)
        start_time = time.perf_counter()

        # Process the request
        resp = self.client.get(
            self.url,
            HTTP_AUTHORIZATION='Token {}'.format(self.admin_token),
        )

        # Get ending stats
        end_time = time.perf_counter()
        end_queries = len(connection.queries)

        # Calculate stats
        total_time = end_time - start_time
        total_queries = end_queries - start_queries

        self.assertGreaterEqual(total_queries, 11)
        self.assertLessEqual(total_queries, 11)

        self.assertGreaterEqual((total_time), 0.03)
        self.assertLessEqual((total_time), 0.08)

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.data['results']), 1)

    @override_settings(
        API_MAX_PAGINATION_SIZE_NESTED=20000,
        DEFAULT_PAGE_SIZE=20000,
        REST_FRAMEWORK={'PAGE_SIZE': 20000, 'PAGINATE_BY': 20000},
    )
    def test_retrieve_for_simple(self):
        for i in range(10000):
            village = Village.objects.create(name=f'vil-{i}')
            village.can_view_users.set([self.admin])
            village.can_admin_groups.set([self.group_can_admin.uid])

        reset_queries()

        # Get beginning stats
        start_queries = len(connection.queries)
        start_time = time.perf_counter()

        resp = self.client.get(
            self.url,
            HTTP_AUTHORIZATION='Token {}'.format(self.admin_token),
        )
        # Get ending stats
        end_time = time.perf_counter()
        end_queries = len(connection.queries)

        # Calculate stats
        total_time = end_time - start_time
        total_queries = end_queries - start_queries

        # print(f"Request: get {self.url}")
        # print(f"Number of Queries: {total_queries}")
        # print(f"Total time: {(total_time):.2f}s")

        self.assertEqual(resp.status_code, 200)

        self.assertGreaterEqual(total_queries, 11)
        self.assertLessEqual(total_queries, 11)

        self.assertGreaterEqual((total_time), 24)
        self.assertLessEqual((total_time), 27)

        self.assertEqual(len(resp.data['results']), 10000)
