# coding: utf-8
from mock import MagicMock, patch
from django.test import TestCase
from django.utils import timezone
import pendulum
from concrete_datastore.api.v1.views import apply_filter_since
from concrete_datastore.routes.views import service_status_view
from django.test import override_settings


@override_settings(DEBUG=True)
class ApiViewsTestCase(TestCase):
    def test_apply_filter_function(self):
        queryset = MagicMock()
        queryset.filter = MagicMock(return_value='queryset_filtered')
        timestamp_start = 123456789
        queryset, timestamp_end = apply_filter_since(queryset, timestamp_start)
        self.assertEqual(queryset, 'queryset_filtered')
        self.assertIn(
            int(timestamp_end),
            [
                int(pendulum.instance(timezone.now()).timestamp()),
                int(pendulum.instance(timezone.now()).timestamp()) - 1,
            ],
        )


@override_settings(DEBUG=True)
class WebAppViewsTestCase(TestCase):
    def test_service_status_view(self):
        import concrete_datastore
        import json

        response = service_status_view('test')
        self.assertDictEqual(
            response._headers,
            {'content-type': ('Content-Type', 'application/json')},
        )
        self.assertEqual(
            json.loads(response._container[0]).get('version'),
            concrete_datastore.__version__,
        )
        self.assertEqual(
            json.loads(response._container[0]).get('api'),
            concrete_datastore.api.v1_1.__version__,
        )


# class PaginatedViewSetTest(TestCase):
#     def setUp(self):
#         pass

#     def test_get_stats(self):
#         view_set = PaginatedViewSet()
#         view_set.get_stats(request=None)
