# coding: utf-8
import logging
import os

from django.conf import settings
from django.dispatch import receiver
from django.db.models.signals import pre_save

from concrete_mailer.preparers import prepare_email

from concrete_datastore.concrete.models import Email  # pylint:disable=E0611


logger = logging.getLogger(__name__)


@receiver(pre_save, sender=Email)
def send_email(sender, instance, **kwargs):
    if instance.resource_status == 'to-send':

        if not instance.subject or not instance.body or not instance.receiver:
            instance.resource_status = 'send-error'
            instance.resource_message = 'Some fields are empty'
            return

        if instance.created_by is None:
            instance.resource_status = 'send-error'
            instance.resource_message = 'No sender available'
            return
        try:
            use_tls = not getattr(settings, 'DEBUG', False)
            email = prepare_email(
                context={"sender_name": settings.EMAIL_SENDER_NAME},
                css=settings.EMAIL_CSS,
                html=instance.body,
                title=instance.subject,
                sender=settings.SERVER_EMAIL,
                recipients=[instance.receiver.email],
                use_tls=use_tls,
                email_host=settings.EMAIL_HOST,
                email_port=settings.EMAIL_PORT,
                email_host_user=settings.EMAIL_HOST_USER,
                email_host_password=settings.EMAIL_HOST_PASSWORD,
            )
            email.send()

            instance.resource_status = 'sent'
            instance.resource_message = 'Mail successfuly sent'
        except Exception:
            logger.exception('Error while sending email')
            instance.resource_status = 'send-error'
            instance.resource_message = 'Unable to send email'


def build_absolute_uri(uri):
    root = '{}://{}:{}/'.format(
        settings.SCHEME, settings.HOSTNAME, settings.PORT
    )
    if uri.startswith('/') and len(uri) > 1:
        uri = uri[1:]
    return os.path.join(root, uri)
