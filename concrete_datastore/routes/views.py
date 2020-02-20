# coding: utf-8
from importlib import import_module

from django.conf import settings
from django.http import JsonResponse, HttpResponse

from rest_framework.views import APIView
from rest_framework.renderers import OpenAPIRenderer

import concrete_datastore
from concrete_datastore.interfaces.openapi_schema_generator import (
    SchemaGenerator,
)


def service_status_view(request):
    plugins = {}
    list_plugins = []
    # Get a unique module
    if isinstance(settings.PLUGINS_TASKS_FUNC, dict):
        list_plugins = settings.PLUGINS_TASKS_FUNC.keys()

        for path_task in list_plugins:
            task_split = path_task.rsplit('.')
            module = import_module(task_split[0])
            plugins[module.__name__] = module.__version__

    return JsonResponse(
        {
            'version': concrete_datastore.__version__,
            'datamodel_version': settings.DATAMODEL_VERSION,
            'api': concrete_datastore.api.v1_1.__version__,
            'plugins': plugins,
            'healthy': True,
            'message': '',
            'name': 'concrete-datastore',
            'license': 'All rights reserved. Netsach 2019.',
        }
    )


class OpenApiView(APIView):
    patterns = None

    def get(self, request, spec_format):
        url_scheme = request._request.META['wsgi.url_scheme']
        try:
            http_host = request._request.META['HTTP_HOST']
        except KeyError:
            http_host = (
                f"{request._request.META['REMOTE_ADDR']}"
                f":{request._request.META['SERVER_PORT']}"
            )

        user_auth_header = request._request.headers.get('Authorization')
        if user_auth_header:
            user_token = user_auth_header.replace('Token ', '')
            from_db = True
        else:
            user_token = None
            from_db = False
        server = f'{url_scheme}://{http_host}'

        generator = SchemaGenerator(
            servers=[server],
            patterns=self.patterns,
            user_token=user_token,
            from_db=from_db,
        )
        schema = generator.get_schema(request=request)

        if spec_format == 'yaml':
            spec = OpenAPIRenderer().render(schema, renderer_context={})
            return HttpResponse(spec.decode())

        return JsonResponse(schema)
