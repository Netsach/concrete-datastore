# coding: utf-8
from mock import MagicMock
import uuid
from rest_framework.test import APITestCase
from collections import OrderedDict
from rest_framework import status
import pendulum

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
    Category,
    ItemPack,
    UniqueTogetherModel,
    DateUtc,
)
from django.test import override_settings
from concrete_datastore.api.v1.datetime import format_datetime


@override_settings(DEBUG=True)
class FilterSupportingComparisonBackendTestCase(APITestCase):
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
        url = '/api/v1.1/auth/login/'
        resp = self.client.post(
            url, {"email": "johndoe@netsach.org", "password": "plop"}
        )
        self.token = resp.data['token']
        for i in range(5):
            Skill.objects.create(name='skill_{}'.format(i), score=i)

    def test_exclusion_filters(self):
        self.assertEqual(Skill.objects.count(), 5)
        resp = self.client.get(
            '/api/v1.1/skill/?score=3',
            HTTP_AUTHORIZATION='Token {}'.format(self.token),
        )
        self.assertEqual(resp.data['objects_count'], 1)
        resp = self.client.get(
            '/api/v1.1/skill/?score!=3&name!=skill_2',
            HTTP_AUTHORIZATION='Token {}'.format(self.token),
        )
        self.assertEqual(resp.data['objects_count'], 3)
        resp = self.client.get(
            '/api/v1.1/skill/?score!=3&name=skill_2',
            HTTP_AUTHORIZATION='Token {}'.format(self.token),
        )
        self.assertEqual(resp.data['objects_count'], 1)

    def test_comparaison_on_integer(self):
        self.assertEqual(Skill.objects.count(), 5)
        resp = self.client.get(
            '/api/v1.1/skill/?score__gte=3',
            HTTP_AUTHORIZATION='Token {}'.format(self.token),
        )
        self.assertEqual(resp.data['objects_count'], 2)
        resp = self.client.get(
            '/api/v1.1/skill/?score__gt=3',
            HTTP_AUTHORIZATION='Token {}'.format(self.token),
        )
        self.assertEqual(resp.data['objects_count'], 1)
        resp = self.client.get(
            '/api/v1.1/skill/?score__lte=1',
            HTTP_AUTHORIZATION='Token {}'.format(self.token),
        )
        self.assertEqual(resp.data['objects_count'], 2)
        resp = self.client.get(
            '/api/v1.1/skill/?score__lt=1',
            HTTP_AUTHORIZATION='Token {}'.format(self.token),
        )
        self.assertEqual(resp.data['objects_count'], 1)
        #: Emty sting raises a ValidationError
        resp = self.client.get(
            '/api/v1/skill/?score__gt=',
            HTTP_AUTHORIZATION='Token {}'.format(self.token),
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertDictEqual(
            resp.data,
            {
                "message": "Attempting to convert an empty string to a date format"
            },
        )

    def test_filter_deciaml_field(self):
        item_1 = ItemPack.objects.create(cost=3.4)
        item_2 = ItemPack.objects.create(cost=3.6)
        resp = self.client.get(
            '/api/v1.1/item-pack/?cost__gt=3.5',
            HTTP_AUTHORIZATION='Token {}'.format(self.token),
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK, msg=resp.data)
        self.assertIn('objects_count', resp.data)
        self.assertEqual(resp.data['objects_count'], 1)
        self.assertEqual(len(resp.data['results']), 1)
        self.assertEqual(resp.data['results'][0]['uid'], str(item_2.pk))


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
        url = '/api/v1.1/auth/login/'
        resp = self.client.post(
            url, {"email": "johndoe@netsach.org", "password": "plop"}
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
            '/api/v1.1/project/',
            HTTP_AUTHORIZATION='Token {}'.format(self.token),
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['objects_count'], 4)

        # Get results with filters name='with space'
        resp = self.client.get(
            '/api/v1.1/project/?name=with%20space',
            HTTP_AUTHORIZATION='Token {}'.format(self.token),
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['objects_count'], 1)

        # Get results with filters name='with space'
        resp = self.client.get(
            '/api/v1.1/project/?name__isempty=true',
            HTTP_AUTHORIZATION='Token {}'.format(self.token),
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['objects_count'], 1)

        resp = self.client.get(
            '/api/v1.1/project/?name__isempty=false',
            HTTP_AUTHORIZATION='Token {}'.format(self.token),
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['objects_count'], 3)

        resp = self.client.get(
            '/api/v1.1/project/?field__isempty=true',
            HTTP_AUTHORIZATION='Token {}'.format(self.token),
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)


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

    def test_filter_with_wrong_fields(self):
        Project.objects.create(
            name="Project1", public=True, description='Test Project'
        )
        Project.objects.create(
            name="Project2", public=True, description='Test Project2'
        )
        requested_filter = 'description'
        resp = self.client.get(
            '/api/v1.1/project/?{}=Test%20Project'.format(requested_filter),
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
            '/api/v1.1/project/?{}__in=Test%20Project,Test%20Project2'.format(
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
            '/api/v1.1/project/?{}__isempty=true'.format(requested_filter),
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
        self.date = pendulum.from_format("2022-2-22", 'YYYY-MM-DD')
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

        resp1 = self.client.post(
            url_date,
            data={
                "date": self.date.add(days=i).to_date_string(),
                "datetime": "2022-02-23T14:00:00.5Z",
            },
            HTTP_AUTHORIZATION="Token {}".format(self.token),
        )
        self.date_utc1_pk = resp1.data['uid']

        resp2 = self.client.post(
            url_date,
            data={
                "date": self.date.add(days=i).to_date_string(),
                "datetime": "2022-02-24T08:45:10.55Z",
            },
            HTTP_AUTHORIZATION="Token {}".format(self.token),
        )
        self.date_utc2_pk = resp2.data['uid']

        resp3 = self.client.post(
            url_date,
            data={
                "date": self.date.add(days=i).to_date_string(),
                "datetime": "2022-02-25T09:30:00Z",
            },
            HTTP_AUTHORIZATION="Token {}".format(self.token),
        )
        self.date_utc3_pk = resp3.data['uid']

        resp4 = self.client.post(
            url_date,
            data={
                "date": self.date.add(days=i).to_date_string(),
                "datetime": "2022-02-25T14:00:00.12345Z",
            },
            HTTP_AUTHORIZATION="Token {}".format(self.token),
        )
        self.date_utc4_pk = resp4.data['uid']

        resp5 = self.client.post(
            url_date,
            data={
                "date": self.date.add(days=i).to_date_string(),
                "datetime": "2022-02-25T14:00:00.999999Z",
            },
            HTTP_AUTHORIZATION="Token {}".format(self.token),
        )
        self.date_utc5_pk = resp5.data['uid']

        resp6 = self.client.post(
            url_date,
            data={
                "date": self.date.add(days=i).to_date_string(),
                "datetime": "2022-02-26T14:00:00Z",
            },
            HTTP_AUTHORIZATION="Token {}".format(self.token),
        )
        self.date_utc6_pk = resp6.data['uid']

        resp7 = self.client.post(
            url_date,
            data={
                "date": self.date.add(days=i).to_date_string(),
                "datetime": "2022-02-26T14:00:03Z",
            },
            HTTP_AUTHORIZATION="Token {}".format(self.token),
        )
        self.date_utc7_pk = resp7.data['uid']

    def tearDown(self):
        pass

    def test_filter_range_date(self):
        """
        Expected:
        self.date_utc2
        self.date_utc3
        self.date_utc4
        self.date_utc5
        """
        start_date = "2022-02-24"
        end_date = "2022-02-25"

        url_date = '/api/v1/date-utc/?datetime__range={},{}'.format(
            start_date, end_date
        )
        results = self.client.get(
            url_date, HTTP_AUTHORIZATION="Token {}".format(self.token)
        )
        self.assertEqual(results.status_code, status.HTTP_200_OK)

        self.assertEqual(len(results.data['results']), 4)
        pks_set = set([result['uid'] for result in results.data['results']])
        self.assertSetEqual(
            pks_set,
            {
                self.date_utc2_pk,
                self.date_utc3_pk,
                self.date_utc4_pk,
                self.date_utc5_pk,
            },
        )

        # Recupere que le self.date_utc2 parce qu'il affiche 1 jour avant la date de fin

    def test_filter_range_datetime(self):
        """
        Expected:
        self.date_utc3
        """
        start_date = "2022-02-25T08:50:00Z"
        end_date = "2022-02-25T09:30:00Z"

        url_date = '/api/v1/date-utc/?datetime__range={},{}'.format(
            start_date, end_date
        )
        results = self.client.get(
            url_date, HTTP_AUTHORIZATION="Token {}".format(self.token)
        )
        self.assertEqual(results.status_code, status.HTTP_200_OK)
        pks_set = set([result['uid'] for result in results.data['results']])

        self.assertEqual(len(results.data['results']), 1)

        self.assertSetEqual(
            pks_set,
            {self.date_utc3_pk},
        )

    def test_filter_range_datetime_same_hour(self):
        """
        Expected:
        self.date_utc4
        self.date_utc5
        """
        start_datetime = "2022-02-25T14:00:00Z"
        end_datetime = "2022-02-25T14:00:00Z"
        url_date = '/api/v1/date-utc/?datetime__range={},{}'.format(
            start_datetime, end_datetime
        )
        results = self.client.get(
            url_date, HTTP_AUTHORIZATION="Token {}".format(self.token)
        )
        self.assertEqual(len(results.data['results']), 2)

        pks_set = set([result['uid'] for result in results.data['results']])

        self.assertSetEqual(
            pks_set,
            {
                self.date_utc4_pk,
                self.date_utc5_pk,
            },
        )

        self.assertEqual(results.status_code, status.HTTP_200_OK)

    def test_filter_gte_datetime(self):
        """
        Expected:
        self.date_utc4
        self.date_utc5
        self.date_utc6
        self.date_utc7
        """
        start_datetime = "2022-02-25T14:00:00Z"
        url_date = '/api/v1/date-utc/?datetime__gte={}'.format(start_datetime)
        results = self.client.get(
            url_date, HTTP_AUTHORIZATION="Token {}".format(self.token)
        )

        pks_set = set([result['uid'] for result in results.data['results']])

        self.assertEqual(results.status_code, status.HTTP_200_OK)
        self.assertEqual(len(results.data['results']), 4)

        self.assertSetEqual(
            pks_set,
            {
                self.date_utc4_pk,
                self.date_utc5_pk,
                self.date_utc6_pk,
                self.date_utc7_pk,
            },
        )

    def test_filter_gte_datetime_microseconds(self):
        """
        Expected:
        self.date_utc4
        self.date_utc5
        self.date_utc6
        self.date_utc7
        """

        start_datetime = "2022-02-25T14:00:00.12345Z"
        url_date = '/api/v1/date-utc/?datetime__gte={}'.format(start_datetime)
        results = self.client.get(
            url_date, HTTP_AUTHORIZATION="Token {}".format(self.token)
        )

        pks_set = set([result['uid'] for result in results.data['results']])

        self.assertEqual(results.status_code, status.HTTP_200_OK)

        self.assertEqual(len(results.data['results']), 4)

        self.assertSetEqual(
            pks_set,
            {
                self.date_utc4_pk,
                self.date_utc5_pk,
                self.date_utc6_pk,
                self.date_utc7_pk,
            },
        )

    def test_filter_gte_datetime_microseconds_2(self):
        """
        Expected:
        self.date_utc5
        self.date_utc6
        self.date_utc7
        """

        start_datetime = "2022-02-25T14:00:00.999999Z"
        url_date = '/api/v1/date-utc/?datetime__gte={}'.format(start_datetime)
        results = self.client.get(
            url_date, HTTP_AUTHORIZATION="Token {}".format(self.token)
        )
        pks_set = set([result['uid'] for result in results.data['results']])

        self.assertEqual(results.status_code, status.HTTP_200_OK)

        self.assertEqual(len(results.data['results']), 3)

        self.assertSetEqual(
            pks_set,
            {
                self.date_utc5_pk,
                self.date_utc6_pk,
                self.date_utc7_pk,
            },
        )

    def test_filter_gt_datetime(self):
        """
        Expected:
        self.date_utc6
        self.date_utc7
        """
        start_datetime = "2022-02-25T14:00:00Z"
        url_date = '/api/v1/date-utc/?datetime__gt={}'.format(start_datetime)
        results = self.client.get(
            url_date, HTTP_AUTHORIZATION="Token {}".format(self.token)
        )
        pks_set = set([result['uid'] for result in results.data['results']])

        self.assertEqual(results.status_code, status.HTTP_200_OK)

        self.assertEqual(len(results.data['results']), 2)

        self.assertSetEqual(
            pks_set,
            {
                self.date_utc6_pk,
                self.date_utc7_pk,
            },
        )

    def test_filter_gt_datetime_microseconds(self):
        """
        Expected:
        self.date_utc5
        self.date_utc6
        self.date_utc7
        """

        start_datetime = "2022-02-25T14:00:00.12345Z"
        url_date = '/api/v1/date-utc/?datetime__gt={}'.format(start_datetime)
        results = self.client.get(
            url_date, HTTP_AUTHORIZATION="Token {}".format(self.token)
        )
        pks_set = set([result['uid'] for result in results.data['results']])

        self.assertEqual(results.status_code, status.HTTP_200_OK)

        self.assertEqual(len(results.data['results']), 3)

        self.assertSetEqual(
            pks_set,
            {
                self.date_utc5_pk,
                self.date_utc6_pk,
                self.date_utc7_pk,
            },
        )

    def test_filter_gt_datetime_microseconds_2(self):
        """
        Expected:
        self.date_utc6
        self.date_utc7
        """

        start_datetime = "2022-02-25T14:00:00.999999Z"
        url_date = '/api/v1/date-utc/?datetime__gt={}'.format(start_datetime)
        results = self.client.get(
            url_date, HTTP_AUTHORIZATION="Token {}".format(self.token)
        )

        pks_set = set([result['uid'] for result in results.data['results']])

        self.assertEqual(results.status_code, status.HTTP_200_OK)

        self.assertEqual(len(results.data['results']), 2)

        self.assertSetEqual(
            pks_set,
            {
                self.date_utc6_pk,
                self.date_utc7_pk,
            },
        )

    def test_filter_lte_datetime(self):
        """
        Expected:
        self.date_utc1
        self.date_utc2
        self.date_utc3
        self.date_utc4
        self.date_utc5
        """

        start_datetime = "2022-02-25T14:00:00Z"
        url_date = '/api/v1/date-utc/?datetime__lte={}'.format(start_datetime)
        results = self.client.get(
            url_date, HTTP_AUTHORIZATION="Token {}".format(self.token)
        )
        pks_set = set([result['uid'] for result in results.data['results']])

        self.assertEqual(results.status_code, status.HTTP_200_OK)

        self.assertEqual(len(results.data['results']), 5)

        self.assertSetEqual(
            pks_set,
            {
                self.date_utc1_pk,
                self.date_utc2_pk,
                self.date_utc3_pk,
                self.date_utc4_pk,
                self.date_utc5_pk,
            },
        )

    def test_filter_lte_datetime_microseconds(self):
        """
        Expected:
        self.date_utc1
        self.date_utc2
        self.date_utc3
        self.date_utc4
        """

        datetime = "2022-02-25T14:00:00.12345Z"
        url_date = '/api/v1/date-utc/?datetime__lte={}'.format(datetime)
        results = self.client.get(
            url_date, HTTP_AUTHORIZATION="Token {}".format(self.token)
        )
        pks_set = set([result['uid'] for result in results.data['results']])

        self.assertEqual(results.status_code, status.HTTP_200_OK)

        self.assertEqual(len(results.data['results']), 4)
        self.assertSetEqual(
            pks_set,
            {
                self.date_utc1_pk,
                self.date_utc2_pk,
                self.date_utc3_pk,
                self.date_utc4_pk,
            },
        )

    def test_filter_lte_datetime_microseconds_2(self):
        """
        Expected:
        self.date_utc1
        self.date_utc2
        self.date_utc3
        self.date_utc4
        self.date_utc5
        """

        datetime = "2022-02-25T14:00:00.999999Z"
        url_date = '/api/v1/date-utc/?datetime__lte={}'.format(datetime)
        results = self.client.get(
            url_date, HTTP_AUTHORIZATION="Token {}".format(self.token)
        )
        pks_set = set([result['uid'] for result in results.data['results']])
        self.assertEqual(results.status_code, status.HTTP_200_OK)

        self.assertEqual(len(results.data['results']), 5)

        self.assertSetEqual(
            pks_set,
            {
                self.date_utc1_pk,
                self.date_utc2_pk,
                self.date_utc3_pk,
                self.date_utc4_pk,
                self.date_utc5_pk,
            },
        )

    def test_filter_lt_datetime(self):
        """
        Expected:
        self.date_utc1
        self.date_utc2
        self.date_utc3
        """

        start_datetime = "2022-02-25T14:00:00Z"
        url_date = '/api/v1/date-utc/?datetime__lt={}'.format(start_datetime)
        results = self.client.get(
            url_date, HTTP_AUTHORIZATION="Token {}".format(self.token)
        )
        self.assertEqual(len(results.data['results']), 3)
        self.assertEqual(results.status_code, status.HTTP_200_OK)

    def test_filter_lt_datetime_microseconds(self):
        """
        Expected:
        self.date_utc1
        self.date_utc2
        self.date_utc3
        self.date_utc4
        """

        start_datetime = "2022-02-25T14:00:00.999999Z"
        url_date = '/api/v1/date-utc/?datetime__lt={}'.format(start_datetime)
        results = self.client.get(
            url_date, HTTP_AUTHORIZATION="Token {}".format(self.token)
        )
        pks_set = set([result['uid'] for result in results.data['results']])
        self.assertEqual(results.status_code, status.HTTP_200_OK)

        self.assertEqual(len(results.data['results']), 4)

        self.assertSetEqual(
            pks_set,
            {
                self.date_utc1_pk,
                self.date_utc2_pk,
                self.date_utc3_pk,
                self.date_utc4_pk,
            },
        )

    def test_filter_lt_datetime_microseconds_2(self):
        """
        Expected:
        self.date_utc1
        self.date_utc2
        self.date_utc3
        """

        start_datetime = "2022-02-25T14:00:00.12345Z"
        url_date = '/api/v1/date-utc/?datetime__lt={}'.format(start_datetime)
        results = self.client.get(
            url_date, HTTP_AUTHORIZATION="Token {}".format(self.token)
        )
        pks_set = set([result['uid'] for result in results.data['results']])
        self.assertEqual(results.status_code, status.HTTP_200_OK)

        self.assertEqual(len(results.data['results']), 3)

        self.assertSetEqual(
            pks_set,
            {
                self.date_utc1_pk,
                self.date_utc2_pk,
                self.date_utc3_pk,
            },
        )

    def test_filter_range_date_with_empty_limits(self):
        start_date = self.date.add(days=-1).to_date_string()
        url_date = '/api/v1/date-utc/?date__range={},'.format(start_date)
        results = self.client.get(
            url_date, HTTP_AUTHORIZATION="Token {}".format(self.token)
        )
        self.assertEqual(results.status_code, status.HTTP_200_OK)

        end_date = self.date.add(days=3).to_date_string()
        url_date = '/api/v1/date-utc/?date__range=,{}'.format(end_date)
        results = self.client.get(
            url_date, HTTP_AUTHORIZATION="Token {}".format(self.token)
        )
        self.assertEqual(results.status_code, status.HTTP_200_OK)

    def test_filter_date_worng_format(self):
        # FORMAT USED: YYYY/MM/DD
        start_date = self.date.add(days=-1).to_date_string().replace('-', '/')
        url_date = '/api/v1/date-utc/?date__range={},'.format(start_date)
        results = self.client.get(
            url_date, HTTP_AUTHORIZATION="Token {}".format(self.token)
        )
        self.assertEqual(results.status_code, status.HTTP_400_BAD_REQUEST)


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
        url = '/api/v1.1/auth/login/'
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
        url_projects = '/api/v1.1/project/'
        # User get only projects from cloisonX
        url_filter = '/api/v1.1/project/?{}={}'.format(
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
        url_filter = '/api/v1.1/project/?{}={}'.format(
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


@override_settings(DEBUG=True)
class FilterUsersByDivider(APITestCase):
    def setUp(self):
        # USER A
        self.user1 = User.objects.create_user('usera@netsach.org')
        self.user1.set_password('plop')
        self.user1.is_staff = True
        self.user1.save()
        confirmation = UserConfirmation.objects.create(user=self.user1)
        confirmation.confirmed = True
        confirmation.save()
        url = '/api/v1.1/auth/login/'
        resp = self.client.post(
            url, {"email": "usera@netsach.org", "password": "plop"}
        )
        self.token_a = resp.data['token']

        # USER B
        self.user2 = User.objects.create_user('userb@netsach.org')
        self.user2.is_staff = True
        self.user2.set_password('plop')
        self.user2.save()
        confirmation = UserConfirmation.objects.create(user=self.user2)
        confirmation.confirmed = True
        confirmation.save()
        url = '/api/v1.1/auth/login/'
        resp = self.client.post(
            url, {"email": "userb@netsach.org", "password": "plop"}
        )
        self.token_b = resp.data['token']

        self.cloisonX = DefaultDivider.objects.create(name="TEST1")
        self.cloisonY = DefaultDivider.objects.create(name="TEST2")

        self.user1.defaultdividers.add(self.cloisonX)

        self.user2.defaultdividers.add(self.cloisonX)
        self.user2.defaultdividers.add(self.cloisonY)

    def test_filter_user_by_divider(self):
        url_user_list = '/api/v1.1/user/'
        # Without entity uid header, returns all users
        resp = self.client.get(
            url_user_list, HTTP_AUTHORIZATION='Token {}'.format(self.token_a)
        )
        self.assertEqual(
            resp.status_code,
            status.HTTP_200_OK,
            # resp.data
        )
        self.assertEqual(resp.data["total_objects_count"], 2)

        # Returns only user 2 that has cloisonY as divider
        resp = self.client.get(
            url_user_list,
            HTTP_AUTHORIZATION='Token {}'.format(self.token_a),
            HTTP_X_ENTITY_UID=str(self.cloisonY.uid),
        )
        self.assertEqual(
            resp.status_code,
            status.HTTP_200_OK,
            # resp.data
        )
        self.assertEqual(resp.data["total_objects_count"], 1)
        self.assertEqual(
            resp.data['results'][0]['verbose_name'], "userb@netsach.org"
        )

        # Returns user 1 and user2, they both have cloisonX as divider
        resp = self.client.get(
            url_user_list,
            HTTP_AUTHORIZATION='Token {}'.format(self.token_a),
            HTTP_X_ENTITY_UID=str(self.cloisonX.uid),
        )
        self.assertEqual(
            resp.status_code,
            status.HTTP_200_OK,
            # resp.data
        )
        self.assertEqual(resp.data["total_objects_count"], 2)

        # Returns 0 users if the divider is not known
        resp = self.client.get(
            url_user_list,
            HTTP_AUTHORIZATION='Token {}'.format(self.token_a),
            HTTP_X_ENTITY_UID=str(uuid.uuid4()),
        )
        self.assertEqual(
            resp.status_code,
            status.HTTP_200_OK,
            # resp.data
        )
        self.assertEqual(resp.data["total_objects_count"], 0)


@override_settings(DEBUG=True)
class FilterWithForeignKeyNone(APITestCase):
    def setUp(self):
        # USER A
        self.user1 = User.objects.create_user('usera@netsach.org')
        self.user1.set_password('plop')
        self.user1.set_level('superuser')
        self.user1.save()
        confirmation = UserConfirmation.objects.create(user=self.user1)
        confirmation.confirmed = True
        confirmation.save()
        url = '/api/v1.1/auth/login/'
        resp = self.client.post(
            url, {"email": "usera@netsach.org", "password": "plop"}
        )
        self.token = resp.data['token']
        self.category1 = Category.objects.create(name='category_test')
        self.skill_1 = Skill.objects.create(
            name='skill_test 1', category=self.category1, score=5
        )
        self.skill_2 = Skill.objects.create(name='skill_test 2', score=5)

    def test_filter_foreign_key_none(self):
        resp = self.client.get(
            '/api/v1.1/skill/',
            data={'category__isnull': 'true'},
            HTTP_AUTHORIZATION='Token {}'.format(self.token),
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["total_objects_count"], 1)
        self.assertEqual(resp.data["results"][0]['name'], 'skill_test 2')

        resp = self.client.get(
            '/api/v1.1/skill/',
            data={'category__isnull': 'false'},
            HTTP_AUTHORIZATION='Token {}'.format(self.token),
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["total_objects_count"], 1)
        self.assertEqual(resp.data["results"][0]['name'], 'skill_test 1')

        resp = self.client.get(
            '/api/v1.1/skill/',
            data={'category__isnull': 'invalid_value'},
            HTTP_AUTHORIZATION='Token {}'.format(self.token),
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["total_objects_count"], 2)


@override_settings(DEBUG=True)
class FilterContainsBackend(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user('user@netsach.org')
        self.user.set_password('plop')
        self.user.set_level('superuser')
        self.user.save()
        confirmation = UserConfirmation.objects.create(user=self.user)
        confirmation.confirmed = True
        confirmation.save()
        url = '/api/v1.1/auth/login/'
        resp = self.client.post(
            url, {"email": "user@netsach.org", "password": "plop"}
        )
        self.token = resp.data['token']

        self.project1 = Project.objects.create(
            name='Project1', description='text of description1'
        )
        self.project1 = Project.objects.create(
            name='Project2', description='text of description2'
        )

    def test_success_exclude_contains(self):
        resp = self.client.get(
            '/api/v1.1/project/',
            data={'name__contains!': '2'},
            HTTP_AUTHORIZATION='Token {}'.format(self.token),
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn('results', resp.data)
        self.assertIn('total_objects_count', resp.data)
        self.assertEqual(resp.data['total_objects_count'], 1)
        names = {project['name'] for project in resp.data['results']}
        self.assertEqual(names, {'Project1'})

    def test_success_combination_filter_and_exclude(self):
        Project.objects.create(name='Project A')
        Project.objects.create(name='Test A')
        Project.objects.create(name='Project ABC')
        Project.objects.create(name='Project B')
        Project.objects.create(name='Test B')
        #: Exclude projects that the name contains "B"
        resp = self.client.get(
            '/api/v1.1/project/',
            data={'name__contains!': 'B'},
            HTTP_AUTHORIZATION='Token {}'.format(self.token),
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn('results', resp.data)
        self.assertIn('total_objects_count', resp.data)
        self.assertEqual(resp.data['total_objects_count'], 4)
        names = {project['name'] for project in resp.data['results']}
        self.assertSetEqual(
            names, {'Project1', 'Project2', 'Project A', 'Test A'}
        )

        #: Filter projects that the name contains "Test"
        resp = self.client.get(
            '/api/v1.1/project/',
            data={'name__contains': 'Test'},
            HTTP_AUTHORIZATION='Token {}'.format(self.token),
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn('results', resp.data)
        self.assertIn('total_objects_count', resp.data)
        self.assertEqual(resp.data['total_objects_count'], 2)
        names = {project['name'] for project in resp.data['results']}
        self.assertSetEqual(names, {'Test B', 'Test A'})

        #: Combine the two querysets
        resp = self.client.get(
            '/api/v1.1/project/',
            data={'name__contains': 'Test', 'name__contains!': 'B'},
            HTTP_AUTHORIZATION='Token {}'.format(self.token),
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn('results', resp.data)
        self.assertIn('total_objects_count', resp.data)
        self.assertEqual(resp.data['total_objects_count'], 1)
        names = {project['name'] for project in resp.data['results']}
        self.assertSetEqual(names, {'Test A'})

    def test_success_one_result_with_contain_filter(self):
        resp = self.client.get(
            '/api/v1.1/project/',
            data={'name__contains': '1'},
            HTTP_AUTHORIZATION='Token {}'.format(self.token),
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn('results', resp.data)
        self.assertIn('total_objects_count', resp.data)
        self.assertEqual(resp.data['total_objects_count'], 1)
        names = {project['name'] for project in resp.data['results']}
        self.assertEqual(names, {'Project1'})

    def test_one_result_with_non_char_field(self):
        resp = self.client.get(
            '/api/v1.1/project/',
            data={'archived__contains': True},
            HTTP_AUTHORIZATION='Token {}'.format(self.token),
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn('results', resp.data)
        self.assertIn('total_objects_count', resp.data)
        self.assertEqual(resp.data['total_objects_count'], 2)
        names = {project['name'] for project in resp.data['results']}
        self.assertEqual(names, {'Project1', 'Project2'})


@override_settings(DEBUG=True)
class FilterInsensitiveContainsBackend(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user('user@netsach.org')
        self.user.set_password('plop')
        self.user.set_level('superuser')
        self.user.save()
        confirmation = UserConfirmation.objects.create(user=self.user)
        confirmation.confirmed = True
        confirmation.save()
        url = '/api/v1.1/auth/login/'
        resp = self.client.post(
            url, {"email": "user@netsach.org", "password": "plop"}
        )
        self.token = resp.data['token']

        self.project1 = Project.objects.create(
            name='Project1', description='text of description1'
        )
        self.project1 = Project.objects.create(
            name='Project2', description='text of description2'
        )
        self.unique_together1 = UniqueTogetherModel.objects.create(
            name='unique_together1', field1='field1'
        )
        self.unique_together2 = UniqueTogetherModel.objects.create(
            name='unique_together2', field1='field1'
        )

    def test_success_one_result_with_icontain_filter(self):
        resp = self.client.get(
            '/api/v1.1/project/',
            data={'name__icontains': 'pRoJeCt1'},
            HTTP_AUTHORIZATION='Token {}'.format(self.token),
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn('results', resp.data)
        self.assertIn('total_objects_count', resp.data)
        self.assertEqual(resp.data['total_objects_count'], 1)
        names = {project['name'] for project in resp.data['results']}
        self.assertEqual(names, {'Project1'})

    def test_exclude_icontains(self):
        resp = self.client.get(
            '/api/v1.1/project/',
            data={'name__icontains!': 'pRoJeCt1'},
            HTTP_AUTHORIZATION='Token {}'.format(self.token),
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn('results', resp.data)
        self.assertIn('total_objects_count', resp.data)
        self.assertEqual(resp.data['total_objects_count'], 1)
        names = {project['name'] for project in resp.data['results']}
        self.assertEqual(names, {'Project2'})

    def test_success_one_result_with_two_icontain_filters(self):
        resp = self.client.get(
            '/api/v1.1/unique-together-model/',
            data={
                'name__icontains': 'uniquE_toGethEr1',
                'field1__icontains': 'fIe',
            },
            HTTP_AUTHORIZATION='Token {}'.format(self.token),
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK, msg=resp.data)
        self.assertIn('results', resp.data)
        self.assertIn('total_objects_count', resp.data)
        self.assertEqual(resp.data['total_objects_count'], 1)
        names = {instance['name'] for instance in resp.data['results']}
        self.assertEqual(names, {'unique_together1'})

    def test_success_one_result_with_two_contain_filters(self):
        resp = self.client.get(
            '/api/v1.1/unique-together-model/',
            data={
                'name__contains': 'unique_together1',
                'field1__contains': 'fie',
            },
            HTTP_AUTHORIZATION='Token {}'.format(self.token),
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK, msg=resp.data)
        self.assertIn('results', resp.data)
        self.assertIn('total_objects_count', resp.data)
        self.assertEqual(resp.data['total_objects_count'], 1)
        names = {instance['name'] for instance in resp.data['results']}
        self.assertEqual(names, {'unique_together1'})


@override_settings(DEBUG=True)
class FilterObjectByUid(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user('user@netsach.org')
        self.user.set_password('plop')
        self.user.set_level('superuser')
        self.user.save()
        confirmation = UserConfirmation.objects.create(user=self.user)
        confirmation.confirmed = True
        confirmation.save()
        url = '/api/v1.1/auth/login/'
        resp = self.client.post(
            url, {"email": "user@netsach.org", "password": "plop"}
        )
        self.token = resp.data['token']

        self.project1 = Project.objects.create(
            name='Project1', description='text of description1'
        )
        self.project2 = Project.objects.create(
            name='Project2', description='text of description2'
        )
        self.project3 = Project.objects.create(
            name='Project3', description='text of description3'
        )
        self.category1 = Category.objects.create(name='category_test')
        self.skill_1 = Skill.objects.create(
            name='skill_test 1', category=self.category1, score=5
        )

    def test_filter_against_uid_field(self):
        resp = self.client.get(
            '/api/v1.1/project/',
            data={'uid__in': f'{self.project1.uid},{self.project3.uid}'},
            HTTP_AUTHORIZATION='Token {}'.format(self.token),
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn('results', resp.data)
        self.assertIn('total_objects_count', resp.data)
        self.assertEqual(resp.data['total_objects_count'], 2)
        names = {project['name'] for project in resp.data['results']}
        self.assertEqual(names, {'Project1', 'Project3'})

    def test_filter_against_uid_with_wrong_uid(self):
        resp = self.client.get(
            '/api/v1.1/project/',
            data={
                'uid__in': f'{self.project1.uid},{self.project3.uid},notanuid'
            },
            HTTP_AUTHORIZATION='Token {}'.format(self.token),
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertDictEqual(
            resp.data, {"message": "uid__in: 'notanuid' is not a valid UUID"}
        )

    def test_filter_against_uid_with_no_values(self):
        resp = self.client.get(
            '/api/v1.1/project/',
            data={'uid__in': ''},
            HTTP_AUTHORIZATION='Token {}'.format(self.token),
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertDictEqual(
            resp.data, {"message": "uid__in: '' is not a valid UUID"}
        )

    def test_filter_against_foreign_key_uid_with_no_values(self):
        resp = self.client.get(
            '/api/v1.1/skill/',
            data={'category__in': ''},
            HTTP_AUTHORIZATION='Token {}'.format(self.token),
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertDictEqual(
            resp.data, {"message": "category__in: '' is not a valid UUID"}
        )
