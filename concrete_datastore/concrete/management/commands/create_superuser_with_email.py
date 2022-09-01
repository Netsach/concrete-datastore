# coding: utf-8

from django.apps import apps
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from concrete_datastore.concrete.management.commands.reset_password import (
    generate_random_password,
    get_admin_url,
)


class Command(BaseCommand):
    help = 'Create users'

    def add_arguments(self, parser):
        parser.add_argument('email', type=str, help='Super user email')

    def handle(self, *args, **options):
        concrete = apps.get_app_config('concrete')
        EmailModel = concrete.models['email']
        UserModel = get_user_model()

        email = options['email'].lower()

        user, created = UserModel.objects.get_or_create(email=email)

        if created:
            password = generate_random_password()
            user.set_password(password)
            user.set_level('superuser')
            user.save()

            admin_url = get_admin_url()
            email_instance = EmailModel(
                created_by=user,
                subject='Access to Concrete Instance',
                body=settings.CREATE_SUPERUSER_EMAIL_MESSAGE_BODY.format(
                    hostname=settings.HOSTNAME,
                    admin_url=admin_url,
                    email=email,
                    password=password,
                ),
                receiver=user,
            )

            email_instance.save()
