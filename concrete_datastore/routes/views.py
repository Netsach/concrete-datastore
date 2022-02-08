# coding: utf-8
from importlib import import_module
import yaml
import json
from django.conf import settings
from django.http import (
    HttpResponse,
    JsonResponse,
    HttpResponseForbidden,
    StreamingHttpResponse,
)

from django.views.generic import TemplateView

from rest_framework.views import APIView
from rest_framework import authentication
from rest_framework.renderers import OpenAPIRenderer
from concrete_datastore.api.v1.authentication import (
    TokenExpiryAuthentication,
    URLTokenExpiryAuthentication,
)
import concrete_datastore
from concrete_datastore.interfaces.yaml_renderer import DatamodelYamlToHtml
from concrete_datastore.interfaces.openapi_schema_generator import (
    SchemaGenerator,
)


def service_status_view(request):
    plugins = {}
    # INSTALLED_PLUGIN is a dict with the plugin/core as key and the
    # version as value
    if isinstance(settings.INSTALLED_PLUGINS, dict):
        plugins = settings.INSTALLED_PLUGINS
    data = {
        'version': concrete_datastore.__version__,
        'datamodel_version': settings.DATAMODEL_VERSION,
        'api': concrete_datastore.api.v1_1.__version__,
        'plugins': plugins,
        'healthy': True,
        'message': '',
        'name': 'concrete-datastore',
        'license': 'All rights reserved. Netsach 2021.',
    }
    if settings.USE_CORE_AUTOMATION:
        try:
            # ImportError if the import fails
            from ns_core.coreApp.models import (  # pylint: disable = import-error
                Parameter,
            )
        except ImportError:
            pass
        else:
            parameter, created = Parameter.objects.get_or_create(
                name='MAINTENANCE_MODE', defaults={'data': {'value': False}}
            )
            maintenance_mode = parameter.data.get('value', False)
            data['maintenance_mode'] = maintenance_mode

    return JsonResponse(data)


class DatamodelServer(APIView, TemplateView):
    template_name = "mainApp/datamodel.html"
    authentication_classes = (
        authentication.BasicAuthentication,
        authentication.SessionAuthentication,
        TokenExpiryAuthentication,
        URLTokenExpiryAuthentication,
    )

    def _get_datamodel_format(self, data_format='yaml'):
        datamodel_content_json = settings.META_MODEL_DEFINITIONS
        if data_format == 'json':
            return json.dumps(datamodel_content_json, indent=4)
        return yaml.dump(datamodel_content_json, allow_unicode=True)

    def get(self, request, *args, **kwargs):
        user = request.user
        if user.is_anonymous or user.is_at_least_admin is False:
            return HttpResponseForbidden()
        action = kwargs.get('action')
        data_format = request.GET.get('data-format', 'yaml').lower()
        if action is None:
            if data_format == 'json':
                return JsonResponse(settings.META_MODEL_DEFINITIONS)
            return HttpResponse(self._get_datamodel_format())
        if action == 'download':
            filename = f'datamodel.{data_format}'
            response = StreamingHttpResponse(
                self._get_datamodel_format(data_format=data_format),
                content_type=data_format,
            )
            response[
                'Content-Disposition'
            ] = 'attachment; filename="{}"'.format(filename)
            return response
        if action == 'view':
            return super().get(request, *args, **kwargs)
        return JsonResponse(
            data={'error': f'unknown action {action}'}, status=400
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        datamodel_content_json = settings.META_MODEL_DEFINITIONS
        context['json_content'] = json.dumps(datamodel_content_json, indent=2)
        datamodel_content_yml = self._get_datamodel_format()
        content = DatamodelYamlToHtml(datamodel_content_json, indent=2)
        context['yaml_displayed_content'] = content.render_yaml()
        context['yaml_content'] = datamodel_content_yml
        return context


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
