# coding: utf-8
from urllib.parse import urljoin

from django.apps import apps
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.conf import settings


class Command(BaseCommand):
    help = 'Invite user to activate OTP'

    def add_arguments(self, parser):
        parser.add_argument(
            'emails', type=str, help='choosen emails, separated by a comma'
        )

    def handle(self, *args, **options):
        UserModel = get_user_model()
        concrete = apps.get_app_config('concrete')
        EmailModel = concrete.models['email']
        emails_str = options['emails'].lower()
        emails = set(emails_str.split(','))

        base_url = f'{settings.SCHEME}://{settings.HOSTNAME}'
        if settings.DEBUG is True:
            base_url += f':{settings.PORT}'
        configure_otp_url = urljoin(base_url, reverse('configure-otp'))
        email_body = settings.SEND_OTP_CONFIGURE_LINK.format(
            platform=settings.PLATFORM_NAME, link=configure_otp_url
        )
        not_found_users = []
        emails_not_sent = []
        has_error = False
        for email in emails:
            try:
                user = UserModel.objects.get(email=email)
            except UserModel.DoesNotExist:
                not_found_users.append(email)
                has_error = True
                continue

            email_instance = EmailModel(
                created_by=user,
                subject=settings.OTP_CONFIGURE_EMAIL_SUBJECT,
                body=email_body,
                receiver=user,
            )

            email_instance.save()
            if email_instance.resource_status == 'send-error':
                emails_not_sent.append(email)
                has_error = True
        if has_error is False:
            print('Emails have been sent')
        if len(not_found_users) > 0:
            emails_list_msg = ", ".join(not_found_users)
            print(f'The following emails do not exist: {emails_list_msg}')
        if len(emails_not_sent) > 0:
            emails_list_msg = ", ".join(emails_not_sent)
            print(
                'An error occured while attempting to send email '
                f'to {emails_list_msg}'
            )
