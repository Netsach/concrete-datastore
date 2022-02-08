# coding: utf-8
from mock import MagicMock
from django.test import TestCase
from concrete_datastore.api.v1.signals import (
    send_email_pre_save,
    build_absolute_uri,
)
from django.test import override_settings


@override_settings(DEBUG=True)
class SignalTests(TestCase):
    def test_build_absolute_uri(self):
        self.assertEqual(
            build_absolute_uri(uri='/uri'), 'http://testserver:80/uri'
        )

    def test_send_mail_failure_unable_to_send(self):
        instance = MagicMock()
        instance.resource_status = 'to-send'
        instance.subject = 'subject'
        instance.body = 'body'
        instance.created_by = 'sender'
        send_email_pre_save(sender='', instance=instance)
