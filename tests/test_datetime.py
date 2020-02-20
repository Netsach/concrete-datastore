# coding: utf-8
from django.utils import timezone
from django.test import TestCase
from concrete_datastore.api.v1.datetime import ensure_pendulum, format_datetime
from django.test import override_settings


@override_settings(DEBUG=True)
class Basic(TestCase):
    def test_parse_string(self):
        now = timezone.now()
        d1 = ensure_pendulum(str(now))
        d2 = ensure_pendulum(now)
        self.assertEqual(format_datetime(d1), format_datetime(d2))
