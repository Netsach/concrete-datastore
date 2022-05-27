# coding: utf-8
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Create users'

    def add_arguments(self, parser):
        parser.add_argument('email', type=str, help='choosen email')
        parser.add_argument('password', type=str, help='choosen password')

    def handle(self, *args, **options):
        UserModel = get_user_model()
        email = options['email'].lower()

        user, created = UserModel.objects.get_or_create(email=email)

        if created:
            user.set_level('superuser')
            if options['password'] is not None:
                user.set_password(options['password'])

            user.save()
