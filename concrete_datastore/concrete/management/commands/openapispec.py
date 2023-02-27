# coding: utf-8
import json

from django.core.management.base import BaseCommand, CommandError

from rest_framework import renderers

from concrete_datastore.interfaces.openapi_schema_generator import (
    SchemaGenerator,
    InvalidTokenUser,
)
from concrete_datastore.routes.urls import (
    urlpatterns as full_urls,
    api_v1_urls,
    api_v1_1_urls,
)

ALLOWED_USER_LEVELS = [
    'superuser',
    'admin',
    'manager',
    'simpleuser',
    'blocked',
]


class Command(BaseCommand):
    help = "Generates configured API schema for project."

    def add_arguments(self, parser):
        parser.add_argument(
            '--format',
            dest="format",
            choices=['yaml', 'json'],
            default='yaml',
            type=str,
            help='Select the OpenAPI Specification format',
        )
        parser.add_argument(
            '--servers',
            dest="servers",
            default=None,
            type=str,
            help=(
                'List of servers on which the server is running.'
                ' Example: ["http://localhost:8000/"]'
            ),
        )
        parser.add_argument(
            '--token',
            dest="user_token",
            default=None,
            type=str,
            help='Token of the user requesting the OpenAPI Specification',
        )
        parser.add_argument(
            '--level',
            dest="user_level",
            choices=ALLOWED_USER_LEVELS,
            default=None,
            type=str,
            help='Level of the user requesting the OpenAPI Specification',
        )
        parser.add_argument(
            '--api_version',
            dest="api_version",
            choices=['v1.1', 'v1', 'all'],
            default='v1.1',
            type=str,
            help='Select the API version for the OpenAPI Specification',
        )

    def handle(self, *args, **options):

        url_patterns_dict = {
            'v1': (api_v1_urls,),
            'v1.1': (api_v1_1_urls,),
            'all': full_urls,
        }
        servers = options['servers']
        if isinstance(servers, str):
            servers = json.loads(servers)

        user_token = options['user_token']

        if user_token is not None and options['user_level'] is not None:
            raise CommandError(
                'You should either select a token or a level, not both'
            )

        #:  if neither user_level not user_token were given
        #:  the default user should be an AnonymousUser which
        #:  matches the permissions of a `blocked` user
        user_level = options['user_level'] or 'blocked'

        #:  These verifications are added so that the unittests pass.
        #:  The `call_command` method does not check if the selected
        #:  option is in the choices list
        if options['format'] not in ['yaml', 'json']:
            raise CommandError('format should be one of yaml, json')
        if options['api_version'] not in ['v1.1', 'v1', 'all']:
            raise CommandError('format should be one of v1.1, v1, all')
        if user_level.lower().strip() not in ALLOWED_USER_LEVELS:
            raise CommandError(
                'level should be one of {}'.format(
                    ', '.join(ALLOWED_USER_LEVELS)
                )
            )

        from_db = user_token is not None

        try:
            generator = SchemaGenerator(
                servers=servers,
                patterns=url_patterns_dict[options['api_version']],
                user_token=user_token,
                user_level=user_level,
                from_db=from_db,
            )
        except InvalidTokenUser:
            raise CommandError(f'Invalid user token {user_token}.')
        schema = generator.get_schema(request=None, public=True)
        renderer = self.get_renderer(spec_format=options['format'])
        output = renderer.render(schema, renderer_context={})
        self.stdout.write(output.decode())

    def get_renderer(self, spec_format):
        renderer_cls = {
            'yaml': renderers.OpenAPIRenderer,
            'json': renderers.JSONOpenAPIRenderer,
        }[spec_format]
        return renderer_cls()
