# coding: utf-8
from urllib.parse import urljoin

from django.apps import apps
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings


class Command(BaseCommand):
    help = 'Invite user to activate OTP'

    def add_arguments(self, parser):
        parser.add_argument('email', type=str, help='choosen email')

    def handle(self, *args, **options):
        UserModel = get_user_model()
        concrete = apps.get_app_config('concrete')
        EmailModel = concrete.models['email']
        email = options['email'].lower()
        try:
            user = UserModel.objects.get(email=email)
        except UserModel.DoesNotExist:
            raise CommandError(f'User with email {email} does not exist')

        base_url = f'{settings.SCHEME}://{settings.HOSTNAME}'
        if settings.DEBUG is True:
            base_url += f':{settings.PORT}'
        configure_otp_url = urljoin(base_url, reverse('configure-otp'))
        email_instance = EmailModel(
            created_by=user,
            subject='Access to Concrete Instance',
            body=settings.SEND_OTP_CONFIGURE_LINK.format(
                platform=settings.PLATFORM_NAME, link=configure_otp_url
            ),
            receiver=user,
        )

        email_instance.save()
