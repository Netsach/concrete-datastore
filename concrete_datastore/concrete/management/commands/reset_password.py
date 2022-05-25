# coding: utf-8
import random
import string

from django.apps import apps
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Reset password'

    def add_arguments(self, parser):
        parser.add_argument('email', type=str, help='user email')

    def handle(self, *args, **options):
        concrete = apps.get_app_config('concrete')
        EmailModel = concrete.models['email']
        UserModel = get_user_model()

        if options['email'] is None:
            raise ValueError("'email' is needed to send your password")

        email = options['email'].lower()

        try:
            user = UserModel.objects.get(email=email)
        except Exception:
            return "This email does not exists"

        password = ''.join(
            random.choice(string.ascii_letters + string.digits)  # nosec
            for _ in range(24)
        )
        user.set_password(password)
        user.save()

        email_instance = EmailModel(
            created_by=user,
            subject='Reset password on concrete',
            body='''
            You have requested a new password
            <br>
            You can now connect to your concrete instance with the following
            password<br>

            password: {password}<br>
            <br>

        '''.format(
                email=email,
                password=password,
            ),
            receiver=user,
        )

        email_instance.save()
