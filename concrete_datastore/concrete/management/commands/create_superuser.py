# coding: utf-8
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Create users'

    def add_arguments(self, parser):
        parser.add_argument('email', type=str, help='choosen email')
        parser.add_argument('--password', type=str, help='raw password')

    def handle(self, *args, **options):
        UserClass = get_user_model()
        kwargs = {
            'email': options['email'].lower(),
            'admin': True,
            'is_superuser': True,
            'is_staff': True,
        }
        instance, created = UserClass.objects.get_or_create(**kwargs)
        if options['password'] is not None:
            instance.set_password(options['password'])
            instance.save()
