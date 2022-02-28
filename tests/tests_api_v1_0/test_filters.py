# coding: utf-8
import pendulum
from mock import MagicMock
from collections import OrderedDict

from django.test import override_settings

from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework.exceptions import ValidationError

from concrete_datastore.api.v1.filters import (
    FilterSupportingOrBackend,
    FilterSupportingRangeBackend,
)
from concrete_datastore.concrete.models import (
    User,
    UserConfirmation,
    Project,
    Skill,
    DefaultDivider,
    DIVIDER_MODEL,
    DateUtc
)


@override_settings(DEBUG=True)
class FilterSupportingComparaisonBackendTestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            'johndoe@netsach.org'
            # 'John',
            # 'Doe',
        )
        self.user.is_superuser = True
        self.user.set_password('plop')
        self.user.save()
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
        for i in range(5):
            Skill.objects.create(name='skill_{}'.format(i), score=i)

    def test_comparaison_on_integer(self):
        self.assertEqual(Skill.objects.count(), 5)
        resp = self.client.get(
            '/api/v1/skill/?score__gte=3',
            HTTP_AUTHORIZATION='Token {}'.format(self.token),
        )
        self.assertEqual(resp.data['objects_count'], 2)
        resp = self.client.get(
            '/api/v1/skill/?score__lte=1',
            HTTP_AUTHORIZATION='Token {}'.format(self.token),
        )
        self.assertEqual(resp.data['objects_count'], 2)
        resp = self.client.get(
            '/api/v1/skill/?score__gt=3',
            HTTP_AUTHORIZATION='Token {}'.format(self.token),
        )
        self.assertEqual(resp.data['objects_count'], 1)
        resp = self.client.get(
            '/api/v1/skill/?score__lt=1',
            HTTP_AUTHORIZATION='Token {}'.format(self.token),
        )
        self.assertEqual(resp.data['objects_count'], 1)


@override_settings(DEBUG=True)
class FilterSupportingOrBackendTestClass(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            'johndoe@netsach.org'
            # 'John',
            # 'Doe',
        )
        self.user.set_password('plop')
        self.user.save()
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

    def tearDown(self):
        pass

    def test_filter_queryset_with_no_q_object(self):
        request = MagicMock()
        view = MagicMock()
        queryset = MagicMock()
        request.query_params = {}
        res = FilterSupportingOrBackend().filter_queryset(
            request=request, queryset=queryset, view=view
        )
        self.assertEqual(res, queryset)

    def test_filter_queryset_with_non_null_query_params(self):
        request = MagicMock()
        view = MagicMock()
        view.filterset_fields = ('field1', 'field2', 'field3')
        queryset = MagicMock()
        request.query_params = OrderedDict(
            [
                ('field1__in', 'value1,value1x'),
                ('field2__in', 'value2,value2x'),
                ('field3__in', 'value3,value3x'),
                ('field4__in', 'value4,value4x'),
                ('field5', 'value5'),
            ]
        )
        res = FilterSupportingOrBackend().filter_queryset(
            request=request, queryset=queryset, view=view
        )
        self.assertNotEqual(res, queryset)

    def test_filter_queryset_with_empty_query_param(self):

        Project.objects.create(name="", public=True)
        Project.objects.create(name=" ", public=True)
        Project.objects.create(name="with space", public=True)
        Project.objects.create(name="with spécials Ch@ars", public=True)
        self.assertEqual(Project.objects.count(), 4)

        # Get all results
        resp = self.client.get(
            '/api/v1/project/',
            HTTP_AUTHORIZATION='Token {}'.format(self.token),
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['objects_count'], 4)

        # Get results with filters name='with space'
        resp = self.client.get(
            '/api/v1/project/?name=with%20space',
            HTTP_AUTHORIZATION='Token {}'.format(self.token),
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['objects_count'], 1)

        # Get results with filters name='with space'
        resp = self.client.get(
            '/api/v1/project/?name__isempty=true',
            HTTP_AUTHORIZATION='Token {}'.format(self.token),
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['objects_count'], 1)
        resp = self.client.get(
            '/api/v1/project/?name__isempty=false',
            HTTP_AUTHORIZATION='Token {}'.format(self.token),
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        # self.assertEqual(resp.data['objects_count'], 0)
        resp = self.client.get(
            '/api/v1/project/?field__isempty=true',
            HTTP_AUTHORIZATION='Token {}'.format(self.token),
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        resp = self.client.get(
            '/api/v1/project/?expected_skills__isempty=true',
            HTTP_AUTHORIZATION='Token {}'.format(self.token),
        )
        #: Returns everything if filter on fk or M2M
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['objects_count'], 4)


@override_settings(DEBUG=True)
class FilterSupportingRangeBackendTestClass(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            'johndoe@netsach.org'
            # 'John',
            # 'Doe',
        )
        self.user.set_password('plop')
        self.user.save()
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

    def tearDown(self):
        pass

    def test_filter_queryset_with_no_q_object(self):
        request = MagicMock()
        view = MagicMock()
        queryset = MagicMock()
        request.query_params = {}
        res = FilterSupportingRangeBackend().filter_queryset(
            request=request, queryset=queryset, view=view
        )
        self.assertEqual(res, queryset)


@override_settings(DEBUG=True)
class FilterWithInvalidFields(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            'johndoe@netsach.org'
            # 'John',
            # 'Doe',
        )
        self.user.set_password('plop')
        self.user.save()
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

    def test_filter_with_wrong_fields(self):
        Project.objects.create(
            name="Project1", public=True, description='Test Project'
        )
        Project.objects.create(
            name="Project2", public=True, description='Test Project2'
        )
        requested_filter = 'description'
        resp = self.client.get(
            '/api/v1/project/?{}=Test%20Project'.format(requested_filter),
            HTTP_AUTHORIZATION='Token {}'.format(self.token),
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertDictEqual(
            resp.data,
            {
                'message': 'filter against {} is not allowed'.format(
                    requested_filter
                ),
                '_errors': ["INVALID_QUERY"],
            },
        )

        resp = self.client.get(
            '/api/v1/project/?{}__in=Test%20Project,Test%20Project2'.format(
                requested_filter
            ),
            HTTP_AUTHORIZATION='Token {}'.format(self.token),
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertDictEqual(
            resp.data,
            {
                'message': 'filter against {} is not allowed'.format(
                    requested_filter
                ),
                '_errors': ["INVALID_QUERY"],
            },
        )

        resp = self.client.get(
            '/api/v1/project/?{}__isempty=true'.format(requested_filter),
            HTTP_AUTHORIZATION='Token {}'.format(self.token),
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertDictEqual(
            resp.data,
            {
                'message': 'filter against {} is not allowed'.format(
                    requested_filter
                ),
                '_errors': ["INVALID_QUERY"],
            },
        )


@override_settings(DEBUG=True)
class FilterDatesTestClass(APITestCase):
    def setUp(self):
        self.user = User.objects.create_superuser(
            email='johndoe@netsach.org',
            password='plop'


            # 'John',
            # 'Doe',
        )

        self.user.save()
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
        self.date = pendulum.from_format("2017-10-28", 'YYYY-MM-DD')
        url_date = '/api/v1/date-utc/'
        for i in range(10):
            self.client.post(
                url_date,
                data={
                    "date": self.date.add(days=i).to_date_string(),
                    "datetime": self.date.add(days=i)
                    .to_iso8601_string()
                    .split('+')[0]
                    + 'Z',
                },
                HTTP_AUTHORIZATION="Token {}".format(self.token),
            )

    def tearDown(self):
        pass

    def test_filter_range_date(self):
        start_date = self.date.add(days=-1).to_date_string()
        end_date = self.date.add(days=3).to_date_string()
        url_date = '/api/v1/date-utc/?date__range={},{}'.format(
            start_date, end_date
        )
        resp = self.client.get(
            url_date, HTTP_AUTHORIZATION="Token {}".format(self.token)
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)


    def test_filter_range_datetime(self):
        date_utc1 = DateUtc.objects.create(datetime=self.date.format('YYYY-MM-DDTHH:mm:ss\Z'))

        end_date_utc2 = self.date.add(minutes=+30)
        date_utc2 = DateUtc.objects.create(datetime=end_date_utc2.format('YYYY-MM-DDTHH:mm:ss\Z'))

        end_date_utc3 = self.date.add(minutes=+50)
        DateUtc.objects.create(datetime=end_date_utc3.format('YYYY-MM-DDTHH:mm:ss\Z'))

        start_datetime = date_utc1.datetime
        end_datetime = date_utc2.datetime
        url_date = '/api/v1/date-utc/?datetime__range={},{}'.format(
            start_datetime, end_datetime
        )
        resp = self.client.get(
            url_date, HTTP_AUTHORIZATION="Token {}".format(self.token)
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        results = resp.json()['results']

        # We don't get the third instance because she is not in the range
        self.assertEqual(len(results), 2)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_filter_range_datetime_fields_with_miliseconds(self):
        start_datetime = "2017-10-27T00:00:00.000000Z"
        end_datetime = "2017-10-30T00:00:00.000000Z"
        url_date = '/api/v1/date-utc/?datetime__range={},{}'.format(
            start_datetime, end_datetime
        )
        resp = self.client.get(
            url_date, HTTP_AUTHORIZATION="Token {}".format(self.token)
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)


    def test_filter_range_datetime_fields_with_miliseconds_wrong_format(self):
        # We pass 7 numbers in milliseconds but we expected 6
        start_datetime = "2017-10-27T00:00:00.0000000Z"
        end_datetime = "2017-10-30T00:00:00.0000000Z"
        url_date = '/api/v1/date-utc/?datetime__range={},{}'.format(
            start_datetime, end_datetime
        )
        resp = self.client.get(
            url_date, HTTP_AUTHORIZATION="Token {}".format(self.token)
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_filter_range_date_with_empty_limits(self):
        start_date = self.date.add(days=-1).to_date_string()
        url_date = '/api/v1/date-utc/?date__range={},'.format(start_date)
        resp = self.client.get(
            url_date, HTTP_AUTHORIZATION="Token {}".format(self.token)
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        end_date = self.date.add(days=3).to_date_string()
        url_date = '/api/v1/date-utc/?date__range=,{}'.format(end_date)
        resp = self.client.get(
            url_date, HTTP_AUTHORIZATION="Token {}".format(self.token)
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_filter_date_worng_format(self):
        # FORMAT USED: YYYY/MM/DD
        start_date = self.date.add(days=-1).to_date_string().replace('-', '/')
        url_date = '/api/v1/date-utc/?date__range={},'.format(start_date)
        resp = self.client.get(
            url_date, HTTP_AUTHORIZATION="Token {}".format(self.token)
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)


@override_settings(DEBUG=True)
class FilterDividedModelByDivider(APITestCase):
    def setUp(self):

        # USER A
        self.user1 = User.objects.create_user('usera@netsach.org')
        self.user1.set_password('plop')
        self.user1.save()
        self.confirmation = UserConfirmation.objects.create(user=self.user1)
        self.confirmation.confirmed = True
        self.confirmation.save()
        url = '/api/v1/auth/login/'
        resp = self.client.post(
            url, {"email": "usera@netsach.org", "password": "plop"}
        )
        self.token_a = resp.data['token']

        self.cloisonX = DefaultDivider.objects.create(name="TEST1")

        self.cloisonY = DefaultDivider.objects.create(name="TEST2")

        self.proj_a = Project.objects.create(
            name="projet A",
            description="tutu",
            defaultdivider=self.cloisonX,
            public=True,
        )

        self.proj_b = Project.objects.create(
            name="projet B",
            description="toto",
            defaultdivider=self.cloisonY,
            public=True,
        )

    def test_filter_objects_by_divider(self):
        url_projects = '/api/v1/project/'
        # User get only projects from cloisonX
        url_filter = '/api/v1/project/?{}={}'.format(
            DIVIDER_MODEL.lower(), str(self.cloisonX.uid)
        )
        resp = self.client.get(
            url_filter, HTTP_AUTHORIZATION='Token {}'.format(self.token_a)
        )
        self.assertEqual(
            resp.status_code, status.HTTP_200_OK, msg=resp.content
        )
        results = resp.json()['results']

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['name'], "projet A")

        # User get only projects from cloisonY
        url_filter = '/api/v1/project/?{}={}'.format(
            DIVIDER_MODEL.lower(), str(self.cloisonY.uid)
        )
        resp = self.client.get(
            url_filter, HTTP_AUTHORIZATION='Token {}'.format(self.token_a)
        )
        self.assertEqual(
            resp.status_code, status.HTTP_200_OK, msg=resp.content
        )
        results = resp.json()['results']

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['name'], "projet B")

        # User get two projects without filter
        resp = self.client.get(
            url_projects, HTTP_AUTHORIZATION='Token {}'.format(self.token_a)
        )
        self.assertEqual(len(resp.json()['results']), 2)
