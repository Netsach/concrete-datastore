# coding: utf-8
import pendulum
from rest_framework.test import APITestCase
from django.conf import settings
from rest_framework import status
from concrete_datastore.concrete.models import (
    User,
    UserConfirmation,
    Project,
)
from django.test import override_settings


@override_settings(DEBUG=True)
class CRUDTestCase(APITestCase):
    def setUp(self):
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
        url = '/api/v1.1/auth/login/'
        resp = self.client.post(
            url, {"email": "johndoe@netsach.org", "password": "plop",},
        )
        self.token = resp.data['token']

    def test_list_project_all(self):
        for i in range(100):
            Project.objects.create(
                name="Project{}".format(i),
                description="description du projet {}".format(i),
                created_by=self.user,
            )

        # PAGINATED RESPONSE
        url_projects = '/api/v1.1/project/'
        resp = self.client.get(
            url_projects, {}, HTTP_AUTHORIZATION='Token {}'.format(self.token)
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn("objects_count", resp.data)
        self.assertIn("next", resp.data)
        self.assertIn("previous", resp.data)
        self.assertIn("results", resp.data)
        self.assertIn("objects_count_per_page", resp.data)
        self.assertIn("num_total_pages", resp.data)
        self.assertIn("num_current_page", resp.data)

        self.assertGreater(100, settings.REST_FRAMEWORK["PAGINATE_BY"])

        self.assertEqual(
            resp.data["objects_count"], settings.API_MAX_PAGINATION_SIZE_NESTED
        )
        self.assertEqual(resp.data["total_objects_count"], 100)
        self.assertEqual(
            resp.data["objects_count_per_page"],
            settings.API_MAX_PAGINATION_SIZE_NESTED,
        )
        # self.assertEqual(resp.data["num_total_pages"], 1)
        self.assertEqual(resp.data["num_current_page"], 1)

        # NOT PAGINATED RESPONSE
        # url_projects = '/api/v1.1/project/all/'
        # resp = self.client.get(url_projects, {
        #     },
        #     HTTP_AUTHORIZATION='Token {}'.format(self.token)
        # )
        # self.assertEqual(resp.status_code, status.HTTP_200_OK)
        # self.assertIn("objects_count", resp.data)
        # self.assertIn("next", resp.data)
        # self.assertIn("previous", resp.data)
        # self.assertIn("results", resp.data)
        # self.assertIn("objects_count_per_page", resp.data)
        # self.assertIn("num_total_pages", resp.data)
        # self.assertIn("num_current_page", resp.data)

        # self.assertGreater(100, settings.REST_FRAMEWORK["PAGINATE_BY"])

        # self.assertEqual(resp.data["objects_count"], 100)
        # self.assertEqual(resp.data["objects_count_per_page"], 100)
        # self.assertEqual(resp.data["num_total_pages"], 1)
        # self.assertEqual(resp.data["num_current_page"], 1)

        # url_projects = '/api/v1.1/project/flat/'
        # resp = self.client.get(url_projects, {
        #     },
        #     HTTP_AUTHORIZATION='Token {}'.format(self.token)
        # )
        # self.assertEqual(resp.status_code, status.HTTP_200_OK)
        # self.assertIn("objects_count", resp.data)
        # self.assertIn("next", resp.data)
        # self.assertIn("previous", resp.data)
        # self.assertIn("results", resp.data)
        # self.assertIn("objects_count_per_page", resp.data)
        # self.assertIn("num_total_pages", resp.data)
        # self.assertIn("num_current_page", resp.data)

        # self.assertGreater(100, settings.REST_FRAMEWORK["PAGINATE_BY"])

        # self.assertEqual(resp.data["objects_count"], 100)
        # self.assertEqual(resp.data["objects_count_per_page"], 100)
        # self.assertEqual(resp.data["num_total_pages"], 1)
        # self.assertEqual(resp.data["num_current_page"], 1)

        # url_projects = '/api/v1.1/project/flat/timestamp_start:123456789.123/'
        # resp = self.client.get(url_projects, {
        #     },
        #     HTTP_AUTHORIZATION='Token {}'.format(self.token)
        # )
        # self.assertEqual(resp.status_code, status.HTTP_200_OK)
        # self.assertIn("objects_count", resp.data)
        # self.assertIn("next", resp.data)
        # self.assertIn("previous", resp.data)
        # self.assertIn("results", resp.data)
        # self.assertIn("objects_count_per_page", resp.data)
        # self.assertIn("num_total_pages", resp.data)
        # self.assertIn("num_current_page", resp.data)

        # self.assertGreater(100, settings.REST_FRAMEWORK["PAGINATE_BY"])

    @override_settings(API_MAX_PAGINATION_SIZE_NESTED=10)
    def test_stats_endpoint(self):
        for i in range(20):
            Project.objects.create(
                name="Project{}".format(i),
                description="description du projet {}".format(i),
                created_by=self.user,
            )
        url_projects = '/api/v1.1/project/stats/?archived=false'
        resp = self.client.get(
            url_projects, {}, HTTP_AUTHORIZATION='Token {}'.format(self.token)
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        self.assertIn('objects_count', resp.data)
        self.assertIn('timestamp_start', resp.data)
        self.assertIn('timestamp_end', resp.data)
        self.assertIn('num_total_pages', resp.data)
        self.assertIn('max_allowed_objects_per_page', resp.data)
        self.assertIn('page_urls', resp.data)

        self.assertEqual(resp.data["objects_count"], 20)
        self.assertEqual(resp.data['timestamp_start'], 0)
        self.assertEqual(resp.data['num_total_pages'], 2)
        self.assertEqual(resp.data['max_allowed_objects_per_page'], 10)

        pages_dict = {
            'page1': 'http://testserver/api/v1.1/project/?archived=false',
            'page2': 'http://testserver/api/v1.1/project/?archived=false&page=2',
        }
        self.assertDictEqual(resp.data['page_urls'], pages_dict)

    @override_settings(API_MAX_PAGINATION_SIZE_NESTED=10)
    def test_stats_endpoint_with_start(self):
        for i in range(20):
            Project.objects.create(
                name="Project{}".format(i),
                description="description du projet {}".format(i),
                created_by=self.user,
            )

        url_projects = '/api/v1.1/project/stats/timestamp_start:123456789.123/'
        resp = self.client.get(
            url_projects, {}, HTTP_AUTHORIZATION='Token {}'.format(self.token)
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        self.assertIn('objects_count', resp.data)
        self.assertIn('timestamp_start', resp.data)
        self.assertIn('timestamp_end', resp.data)
        self.assertIn('num_total_pages', resp.data)
        self.assertIn('max_allowed_objects_per_page', resp.data)
        self.assertIn('page_urls', resp.data)

        self.assertEqual(resp.data['objects_count'], 20)
        self.assertEqual(resp.data['timestamp_start'], '123456789.123')
        self.assertEqual(resp.data['num_total_pages'], 2)
        self.assertEqual(resp.data['max_allowed_objects_per_page'], 10)

        pages_dict = {
            'page1': 'http://testserver/api/v1.1/project/?timestamp_start=123456789.123',
            'page2': 'http://testserver/api/v1.1/project/?page=2&timestamp_start=123456789.123',
        }
        self.assertDictEqual(resp.data['page_urls'], pages_dict)

    @override_settings(API_MAX_PAGINATION_SIZE_NESTED=10)
    def test_stats_endpoint_start_end(self):
        for i in range(20):
            Project.objects.create(
                name="Project{}".format(i),
                description="description du projet {}".format(i),
                created_by=self.user,
            )

        ts = pendulum.now('utc').timestamp()

        url_projects = f'/api/v1.1/project/stats/timestamp_start:123456789.123-timestamp_end:{ts}/'
        resp = self.client.get(
            url_projects, {}, HTTP_AUTHORIZATION='Token {}'.format(self.token)
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        self.assertIn('objects_count', resp.data)
        self.assertIn('timestamp_start', resp.data)
        self.assertIn('timestamp_end', resp.data)
        self.assertIn('num_total_pages', resp.data)
        self.assertIn('max_allowed_objects_per_page', resp.data)
        self.assertIn('page_urls', resp.data)

        self.assertEqual(resp.data['objects_count'], 20)
        self.assertEqual(resp.data['timestamp_start'], '123456789.123')
        self.assertEqual(resp.data['num_total_pages'], 2)
        self.assertEqual(resp.data['max_allowed_objects_per_page'], 10)

        pages_dict = {
            'page1': f'http://testserver/api/v1.1/project/?timestamp_end={ts}&timestamp_start=123456789.123',
            'page2': f'http://testserver/api/v1.1/project/?page=2&timestamp_end={ts}&timestamp_start=123456789.123',
        }
        self.assertDictEqual(resp.data['page_urls'], pages_dict)

    @override_settings(API_MAX_PAGINATION_SIZE_NESTED=10)
    def test_stats_endpoint_start_end_archived(self):
        for i in range(20):
            Project.objects.create(
                name="Project{}".format(i),
                description="description du projet {}".format(i),
                created_by=self.user,
            )

        ts = pendulum.now('utc').timestamp()

        url_projects = f'/api/v1.1/project/stats/timestamp_start:123456789.123-timestamp_end:{ts}/?archived=false'
        resp = self.client.get(
            url_projects, {}, HTTP_AUTHORIZATION='Token {}'.format(self.token)
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        self.assertIn('objects_count', resp.data)
        self.assertIn('timestamp_start', resp.data)
        self.assertIn('timestamp_end', resp.data)
        self.assertIn('num_total_pages', resp.data)
        self.assertIn('max_allowed_objects_per_page', resp.data)
        self.assertIn('page_urls', resp.data)

        self.assertEqual(resp.data['objects_count'], 20)
        self.assertEqual(resp.data['timestamp_start'], '123456789.123')
        self.assertEqual(resp.data['num_total_pages'], 2)
        self.assertEqual(resp.data['max_allowed_objects_per_page'], 10)

        pages_dict = {
            'page1': f'http://testserver/api/v1.1/project/?archived=false&timestamp_end={ts}&timestamp_start=123456789.123',
            'page2': f'http://testserver/api/v1.1/project/?archived=false&page=2&timestamp_end={ts}&timestamp_start=123456789.123',
        }
        self.assertDictEqual(resp.data['page_urls'], pages_dict)

    def test_list_projects_error_wrong_date(self):
        resp = self.client.post(
            "/api/v1.1/date-utc/",
            data={"datetime": "2018-05-07T12:44:29Z"},
            HTTP_AUTHORIZATION='Token {}'.format(self.token),
        )

        # PAGINATED RESPONSE
        url_projects = (
            '/api/v1.1/date-utc/?datetime__range=11/12/2002,10/12/2020'
        )
        resp = self.client.get(
            url_projects, {}, HTTP_AUTHORIZATION='Token {}'.format(self.token)
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('_errors', resp.data)
        self.assertEqual(resp.data['_errors'], ['INVALID_QUERY'])

    def test_list_projects_error_wrong_filter(self):
        Project.objects.create(
            name="Project{}".format(1),
            description="description du projet {}".format(1),
            created_by=self.user,
        )

        # PAGINATED RESPONSE
        url_projects = '/api/v1.1/project/?description__isempty=true'
        resp = self.client.get(
            url_projects, {}, HTTP_AUTHORIZATION='Token {}'.format(self.token)
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('_errors', resp.data)
        self.assertEqual(resp.data['_errors'], ['INVALID_QUERY'])
        self.assertEqual(
            resp.data['message'], 'filter against description is not allowed'
        )

    def test_CRUD_Project(self):
        url_projects = '/api/v1.1/project/'

        self.assertEqual(Project.objects.count(), 0)

        # CREATE a valid project and ensure that request is valid(202)
        resp = self.client.post(
            url_projects,
            {
                "name": "Projects2",
                # "date_creation": timezone.now(),
                "description": "description de mon projet",
                "skills": [],
                "members": [],
            },
            HTTP_AUTHORIZATION='Token {}'.format(self.token),
        )
        self.assertEqual(
            resp.status_code, status.HTTP_201_CREATED, msg=resp.content
        )
        self.assertEqual(Project.objects.count(), 1)

        self.assertIn("url", resp.data)
        url = resp.data['url']

        self.assertIn("uid", resp.data)
        uid = resp.data['uid']

        # RETRIEVE the previous created project (http 200 if ok)
        resp = self.client.get(
            url, {}, HTTP_AUTHORIZATION='Token {}'.format(self.token)
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        # UPDATE to change the project name
        resp = self.client.patch(
            url,
            {"name": "Project42"},
            HTTP_AUTHORIZATION='Token {}'.format(self.token),
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        new_name = resp.data['name']
        self.assertEqual(new_name, "Project42", msg=resp.content)
        p = Project.objects.get(uid=uid)
        self.assertEqual(p.name, new_name, msg=p)

        #: Test prefetching models
        queryset = Project.objects.all().prefetch_related(
            'can_view_users',
            'can_view_groups',
            'can_admin_users',
            'can_admin_groups',
        )
        # list(queryset.values_list('uid', flat=True))

        # DELETE the project
        resp = self.client.delete(
            url, {}, HTTP_AUTHORIZATION='Token {}'.format(self.token)
        )
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Project.objects.count(), 0)

        # Unicode project for coverage
        proj = Project(
            name="ProjCover", description="description de mon projet"
        )
        self.assertIsInstance(str(proj), str)
        self.assertNotEqual(str(proj), "")
