# coding: utf-8
import random
import string

from django.apps import apps
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.core.management.base import CommandError


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

        password = ''.join(
            random.choice(string.ascii_letters + string.digits)  # nosec
            for _ in range(24)
        )
        user.set_password(password)
        user.save()

        port = ''
        if int(settings.PORT) not in (80, 443):
            port = ':{}'.format(settings.PORT)

        admin_url = '{}://{}{}/concrete-datastore-admin/'.format(
            settings.SCHEME, settings.HOSTNAME, port
        )

        email_instance = EmailModel(
            created_by=user,
            subject='Reset password to Concrete Instance',
            body='''
            Welcome to Concrete <a href="{admin_url}">{hostname}</a><br>
                <br>
                You have requested a new password.
                You can now connect to your concrete instance with the following
                credentials :<br>

                email {email}<br>
                password {password}<br>
                <br>
                Please change your password as you connect for the first time.

        '''.format(
                hostname=settings.HOSTNAME,
                admin_url=admin_url,
                email=email,
                password=password,
            ),
            receiver=user,
        )

        email_instance.save()
