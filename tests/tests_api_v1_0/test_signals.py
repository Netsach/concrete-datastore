# coding: utf-8
from mock import MagicMock, patch
from django.test import TestCase
from concrete_datastore.api.v1.signals import (
    send_email_pre_save,
    build_absolute_uri,
)
from concrete_datastore.concrete.models import Email, User
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

    @override_settings(CELERY_ALWAYS_EAGER=True, SMTP_MAILING_USE_ASYNC=True)
    def test_send_email_async_no_body(self):
        email = Email.objects.create(resource_status='to-send')
        email.refresh_from_db()
        self.assertEqual(email.resource_status, 'send-error')
        self.assertEqual(email.resource_message, 'Some fields are empty')

    @override_settings(CELERY_ALWAYS_EAGER=True, SMTP_MAILING_USE_ASYNC=True)
    def test_send_email_async_no_sender(self):
        user = User.objects.create(email='test@netsach.org')
        email = Email.objects.create(
            resource_status='to-send',
            body='test',
            receiver=user,
            subject='test',
        )
        email.refresh_from_db()
        self.assertEqual(email.resource_status, 'send-error')
        self.assertEqual(email.resource_message, 'No sender available')

    @override_settings(
        CELERY_ALWAYS_EAGER=True,
        SMTP_MAILING_USE_ASYNC=True,
        EMAIL_HOST='localhost',
        EMAIL_PORT=1025,
        EMAIL_HOST_USER='',
        EMAIL_HOST_PASSWORD='',
    )
    def test_send_email_async_success(self):
        user = User.objects.create(email='test@netsach.org')
        email = Email.objects.create(
            resource_status='to-send',
            body='test',
            receiver=user,
            subject='test',
            created_by=user,
        )
        email.refresh_from_db()
        self.assertEqual(email.resource_status, 'sent')
        self.assertEqual(email.resource_message, 'Mail successfuly sent')
