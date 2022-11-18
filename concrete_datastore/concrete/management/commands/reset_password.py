# coding: utf-8
import random
import string

from django.apps import apps
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.core.management.base import CommandError


def generate_random_password(
    length=24, chars=string.ascii_letters + string.digits
):
    return ''.join(random.choice(chars) for _ in range(length))  # nosec


def get_admin_url():
    port = ''
    if int(settings.PORT) not in (80, 443):
        port = ':{}'.format(settings.PORT)

    admin_url = '{}://{}{}/concrete-datastore-admin/'.format(
        settings.SCHEME, settings.HOSTNAME, port
    )
    return admin_url


class Command(BaseCommand):
    help = 'Reset password'

    def add_arguments(self, parser):
        parser.add_argument('email', type=str, help='user email')

    def handle(self, *args, **options):
        concrete = apps.get_app_config('concrete')
        EmailModel = concrete.models['email']
        UserModel = get_user_model()
        email = options['email'].lower()

        try:
            user = UserModel.objects.get(email=email)
        except UserModel.DoesNotExist:
            raise CommandError(f"This email: {email} does not exist")

        password = generate_random_password()
        user.set_password(password)
        user.save()

        admin_url = get_admin_url()
        email_instance = EmailModel(
            created_by=user,
            subject='Reset password to Concrete Instance',
            body=settings.RESET_PASSWORD_EMAIL_MESSAGE_BODY.format(
                hostname=settings.HOSTNAME,
                admin_url=admin_url,
                email=email,
                password=password,
            ),
            receiver=user,
        )

        email_instance.save()
