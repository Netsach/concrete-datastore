# coding: utf-8
import logging
from importlib import import_module
from tenacity import (
    Retrying,
    wait_fixed,
    retry_if_exception_type,
    stop_after_attempt,
)

from django.conf import settings

from concrete_datastore.settings.celery import app
from concrete_mailer.preparers import prepare_email

from concrete_datastore.concrete.models import Email  # pylint:disable=E0611

logger = logging.getLogger(__name__)


@app.task
def async_run_plugin_tasks():
    if isinstance(settings.PLUGINS_TASKS_FUNC, dict) is False:
        return
    for path_task, queue in settings.PLUGINS_TASKS_FUNC.items():
        module_name, func_name = path_task.rsplit('.', 1)
        module = import_module(module_name)
        function = getattr(module, func_name)
        function.apply_async(queue=queue)


@app.task
def send_async_mails(email_pk):
    email = Email.objects.get(pk=email_pk)
    perform_send_email(instance=email, is_async=True)


def save_instance_if_async(instance, is_async):
    #: If this method is callled from an async process, save the instance
    #: Otherwise, this method is called directly from the pre_save
    #: signal and the instance will be saved after the signal
    if is_async is True:
        instance.save()


def perform_send_email(instance, enable_retrying=True, is_async=False):
    def _perform_send_email():
        #: Refresh instance
        if not instance.subject or not instance.body or not instance.receiver:
            instance.resource_status = 'send-error'
            instance.resource_message = 'Some fields are empty'
            save_instance_if_async(instance=instance, is_async=is_async)
            return

        if instance.created_by is None:
            instance.resource_status = 'send-error'
            instance.resource_message = 'No sender available'
            save_instance_if_async(instance=instance, is_async=is_async)
            return
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
        save_instance_if_async(instance=instance, is_async=is_async)

    try:
        if enable_retrying is False:
            _perform_send_email()
        else:
            send_email_retryer = Retrying(
                retry=retry_if_exception_type(),
                wait=wait_fixed(settings.RETRYING_DELAY_SECONDS),
                stop=stop_after_attempt(settings.MAX_RETRIES),
            )
            send_email_retryer(_perform_send_email)
    except Exception as e:
        logger.info(
            f'ERROR : Unable to send email {instance.pk} '
            f'to {instance.receiver.email}, {str(e)}'
        )
        instance.resource_status = 'send-error'
        instance.resource_message = 'Unable to send email'
        save_instance_if_async(instance=instance, is_async=is_async)
