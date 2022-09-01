# coding: utf-8

from django.conf import settings
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = (
        'Get db connection string, could be used with pg_dump,'
        '`pg_dump --dbname=$CONNECTION_STRING`'
        'see https://www.postgresql.org/docs/14/libpq-connect.html'
    )

    def get_pg_dump_params(self):
        db_host = settings.DATABASES['default']['HOST']
        db_port = settings.DATABASES['default']['PORT']
        db_user = settings.DATABASES['default']['USER']
        db_name = settings.DATABASES['default']['NAME']
        db_pwd = settings.DATABASES['default']['PASSWORD']
        return f'postgresql://{db_user}:{db_pwd}@{db_host}:{db_port}/{db_name}'

    def handle(self, *args, **options):
        self.stdout.write(self.get_pg_dump_params())
