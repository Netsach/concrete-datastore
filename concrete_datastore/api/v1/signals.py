# coding: utf-8
import logging
import os

from django.conf import settings
from django.dispatch import receiver
from django.db.models.signals import pre_save, post_save

from concrete_datastore.concrete.models import Email  # pylint:disable=E0611
from concrete_datastore.concrete.automation.tasks import (
    send_async_mails,
    perform_send_email,
)


logger = logging.getLogger(__name__)


@receiver(post_save, sender=Email)
def send_email_post_save(sender, instance, **kwargs):
    #: If SMTP_MAILING_USE_ASYNC is enabled, the async task should be in a
    #: post_save signal, because the instance should exist
    if (
        instance.resource_status == 'to-send'
        and settings.SMTP_MAILING_USE_ASYNC is True
    ):
        send_async_mails.apply_async(
            queue='email_senders', kwargs={"email_pk": str(instance.pk)}
        )


@receiver(pre_save, sender=Email)
def send_email_pre_save(sender, instance, **kwargs):
    if (
        instance.resource_status == 'to-send'
        and settings.SMTP_MAILING_USE_ASYNC is False
    ):
        perform_send_email(
            instance=instance,
            enable_retrying=settings.RETRY_ON_SENDING_SYNC_EMAILS,
        )


def build_absolute_uri(uri):
    root = '{}://{}:{}/'.format(
        settings.SCHEME, settings.HOSTNAME, settings.PORT
    )
    if uri.startswith('/') and len(uri) > 1:
        uri = uri[1:]
    return os.path.join(root, uri)
