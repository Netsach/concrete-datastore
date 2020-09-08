# coding: utf-8
import uuid
import warnings
import logging
from urllib.parse import urljoin

from django.db import models
from django.core import validators
from django.http import HttpRequest
from django.conf import settings
from django.utils.encoding import force_text

from rest_framework import exceptions, serializers
from rest_framework.fields import empty
from rest_framework.compat import uritemplate
from rest_framework.request import Request
from rest_framework.schemas.utils import get_pk_description
from rest_framework.schemas.openapi import AutoSchema as AutoSchemaSuper
from rest_framework.schemas.generators import (
    EndpointEnumerator,
    BaseSchemaGenerator as BaseSchemaSuper,
)

import concrete_datastore


logger = logging.getLogger('open-api-spec')

CONCRETE_FAIL_RESPONSES = {
    '404': {'description': 'Not found'},
    '400': {'description': 'Bad request'},
    '401': {'description': 'Unauthorized'},
    '403': {'description': 'Forbidden'},
    '429': {'description': 'Too many requests'},
    '412': {'description': 'Precondition failed'},
}

CONCRETE_DEFAULT_LIST_RESP = {
    'objects_count': {'type': 'integer'},
    'next': {'type': 'string'},
    'previous': {'type': 'string'},
    'objects_count_per_page': {'type': 'integer'},
    'num_total_pages': {'type': 'integer'},
    'num_current_page': {'type': 'integer'},
    'max_allowed_objects_per_page': {'type': 'integer'},
    'model_name': {'type': 'string'},
    'model_verbose_name': {'type': 'string'},
    'list_display': {'type': 'array', 'items': {'type': 'string'}},
    'list_filter': {'type': 'array', 'items': {'type': 'object'}},
    'total_objects_count': {'type': 'integer'},
    'create_url': {'type': 'string'},
}

SWAGGER_SETTINGS = {
    'APP_VERSION': concrete_datastore.__version__,
    'DESCRIPTION': 'Concrete datastore API.',
    'CONTACT': {'email': 'contact@netsach.org'},
    'TERMS_OF_SERVICE': '',
    'SECURITY_DEFINITIONS': {
        'Token': {'type': 'apiKey', 'in': 'header', 'name': 'Authorization'}
    },
}


class InvalidTokenUser(Exception):
    pass


class HasPermissionFakeUser:
    def __init__(self, level):
        level = level.lower().strip()
        self.pk = uuid.uuid4()
        self.is_anonymous = level == 'blocked'
        self.is_authenticated = self.is_anonymous is False
        self.is_superuser = level == 'superuser'
        self.admin = self.is_superuser or level == 'admin'
        self.is_staff = self.admin or level == 'manager'
        self.is_active = self.is_staff or level == 'simpleuser'
        self.is_at_least_admin = self.admin
        self.is_at_least_staff = self.admin or self.is_staff

    def get_roles(self):
        if self.is_anonymous is False:
            logger.info(
                f'Project requires to access User Roles, but we are'
                ' trying to generate the specification without any'
                ' Database for a user with "{self.level}" level.'
            )
        return []

    @property
    def level(self):
        if self.is_superuser:
            return 'superuser'
        if self.admin:
            return 'admin'
        if self.is_staff:
            return 'manager'
        if self.is_active:
            return 'simpleuser'
        return 'blocked'

    def is_confirmed(self):
        return self.is_active

    def get_level(self):
        if self.is_superuser:
            return 'SuperUser'
        if self.admin:
            return 'Admin'
        if self.is_staff:
            return 'Manager'
        if self.is_active:
            return 'SimpleUser'
        return 'Blocked'


class CustomEndpointEnumerator(EndpointEnumerator):
    def get_allowed_methods(self, callback):
        """
        Return a list of the valid HTTP methods for this endpoint.
        """
        if hasattr(callback, 'actions'):
            actions = set(callback.actions)
            methods = [method.upper() for method in actions]
        else:
            #:  Some views require a api_namespace attribute
            kwargs = getattr(callback, 'view_initkwargs', {})
            methods = callback.cls(**kwargs).allowed_methods

        return [
            method for method in methods if method not in ('OPTIONS', 'HEAD')
        ]


class BaseSchemaGenerator(BaseSchemaSuper):
    endpoint_inspector_cls = CustomEndpointEnumerator
    urlconf = None
    url = None
    endpoints = None

    def __init__(
        self,
        patterns=None,
        servers=None,
        user_token=None,
        from_db=False,
        user_level='blocked',
    ):
        super().__init__(
            title=settings.OPENAPI_SPEC_TITLE,
            patterns=patterns,
            description=SWAGGER_SETTINGS['DESCRIPTION'],
        )

        license_content = getattr(settings, 'LICENSE')

        self.title = settings.OPENAPI_SPEC_TITLE
        self.license = {'name': license_content} if license_content else {}
        self.terms_of_service = SWAGGER_SETTINGS['TERMS_OF_SERVICE']
        self.version = SWAGGER_SETTINGS['APP_VERSION']
        self.security_definitions = SWAGGER_SETTINGS['SECURITY_DEFINITIONS']
        self.contact = SWAGGER_SETTINGS['CONTACT']
        self.servers = servers
        self.from_db = from_db
        self.user = self._get_user(token=user_token, level=user_level)

    def _get_user(self, token, level):
        if self.from_db is False:
            return HasPermissionFakeUser(level=level)

        #:  AuthToken is imported only if `self.from_db` is True in order
        #:  to avoid any database errors
        from concrete_datastore.concrete.models import AuthToken

        # pylint: disable=no-member
        user_token = AuthToken.objects.filter(pk=token).first()
        if user_token:
            return user_token.user
        raise InvalidTokenUser()

    def _get_paths_and_endpoints(self, request):
        """
        Generate (path, method, view) given (path, method, callback) for paths.
        """
        paths = []
        view_endpoints = []
        for path, method, callback in self.endpoints:
            view = self.create_view(callback, method, request)
            path = self.coerce_path(path, method, view)
            path = path.replace('\\', '')
            paths.append(path)
            view_endpoints.append((path, method, view))

        return paths, view_endpoints

    def coerce_path(self, path, method, view):
        if not self.coerce_path_pk:
            return path
        return path.replace('{pk}', '{uid}')

    def has_view_permissions(self, path, method, view):
        """
        Return `True` if the incoming request has the correct view permissions.
        """
        request = view.request
        if request is None:
            request = Request(HttpRequest())
            setattr(request, 'method', method)
            setattr(request, 'user', self.user)
            setattr(view, 'request', request)
        elif isinstance(self.user, HasPermissionFakeUser):
            setattr(request, 'user', self.user)

        for permission_cls in view.permission_classes:
            if not permission_cls().has_permission(request, view):
                return False
        return True


def filter_empty(data):
    if isinstance(data, dict):
        return {
            key: filter_empty(value) for key, value in data.items() if value
        }
    if isinstance(data, (list, set, tuple)):
        return list(map(filter_empty, data))
    else:
        return data


# Generator
class SchemaGenerator(BaseSchemaGenerator):
    def get_info(self):
        info = {
            "title": self.title,
            "description": self.description,
            "termsOfService": self.terms_of_service,
            "contact": self.contact,
            "license": self.license,
            "version": self.version,
        }
        return info

    def get_paths_and_components(self, request=None):
        result_path = {}
        result_components = {}

        paths, view_endpoints = self._get_paths_and_endpoints(request)

        # Only generate the path prefix for paths that will be included
        if not paths:
            return None

        for path, method, view in view_endpoints:
            if not self.has_view_permissions(path, method, view):
                continue
            operation = view.schema.get_operation(
                path=path, method=method, from_db=self.from_db
            )
            components = view.schema.get_component_schemas()
            # Normalise path for any provided mount url.
            if path.startswith('/'):
                path = path[1:]
            path = urljoin(self.url or '/', path)

            result_path.setdefault(path, {})
            result_path[path][method.lower()] = operation
            result_components.update(components)

        return result_path, result_components

    def get_schema(self, request=None, public=False):
        """
        Generate a OpenAPI schema.
        """
        self._initialise_endpoints()

        paths, components = self.get_paths_and_components(
            None if public else request
        )
        if not paths:
            return None

        schema_servers = {}
        if self.servers:
            schema_servers = {
                'servers': [{'url': server} for server in self.servers]
            }
        schema = {
            'openapi': '3.0.2',
            'info': filter_empty(self.get_info()),
            **schema_servers,
            'security': [
                {security: []} for security in self.security_definitions.keys()
            ],
            'paths': filter_empty(paths),
            'components': {
                'schemas': filter_empty(components),
                'securitySchemes': filter_empty(self.security_definitions),
            },
        }
        return schema


class AutoSchema(AutoSchemaSuper):

    operation_ids = set()
    components = {}

    def get_component_schemas(self):
        return self.components

    def get_operation(self, path, method, from_db):
        operation = {}

        operation['operationId'] = self.get_distinct_operation_id(
            self._get_operation_id(path, method)
        )
        if from_db is False:
            self.view.get_queryset = lambda: None

        parameters = []
        parameters += self.get_custom_path_parameters(path, method)
        parameters += self._get_pagination_parameters(path, method)
        parameters += self._get_filter_parameters(path, method)
        operation['parameters'] = parameters

        request_body = self.get_custom_request_body(path, method)
        if request_body:
            operation['requestBody'] = request_body
        operation['responses'] = self.get_custom_responses(path, method)

        return operation

    def get_distinct_operation_id(self, op_id):
        # Ensure operation Id is unique by incrementing the suffix
        if op_id not in self.operation_ids:
            self.operation_ids.add(op_id)
            return op_id

        inc = 1
        while f'{op_id}_{inc}' in self.operation_ids:
            inc += 1

        op_id = f'{op_id}_{inc}'
        self.operation_ids.add(op_id)
        return op_id

    def get_custom_path_parameters(self, path, method):
        """
        Return a list of parameters from templated path variables.
        """
        model = getattr(self.view.__class__, 'model_class', None)

        parameters = []
        for variable in uritemplate.variables(path):
            description = ''
            if model is not None:
                # Attempt to infer a field description if possible.
                try:
                    model_field = model._meta.get_field(variable)
                except Exception:
                    model_field = None

                if model_field is not None and model_field.help_text:
                    description = force_text(model_field.help_text)
                elif model_field is not None and model_field.primary_key:
                    description = get_pk_description(model, model_field)

            parameter = {
                "name": variable,
                "in": "path",
                "required": True,
                "description": description,
                'schema': {'type': 'string'},
            }
            parameters.append(parameter)

        return parameters

    def custom_map_field(self, field):

        if isinstance(field, serializers.ListSerializer):
            comp_name = self.get_component_name(path=None, serializer=field)
            if comp_name not in self.components.keys():
                self.components.update(
                    {comp_name: self.custom_map_serializer(field.child)}
                )
            return {
                'type': 'array',
                'items': {'$ref': f'#/components/schemas/{comp_name}'},
            }
        if isinstance(field, serializers.Serializer):
            comp_name = self.get_component_name(path=None, serializer=field)
            if comp_name not in self.components.keys():
                self.components.update(
                    {comp_name: self.custom_map_serializer(field)}
                )
            return {'$ref': f'#/components/schemas/{comp_name}'}

        # Related fields.
        if isinstance(field, serializers.ManyRelatedField):
            return {
                'type': 'array',
                'items': {'type': 'string', 'format': 'uid'},
            }

        if isinstance(field, serializers.PrimaryKeyRelatedField):
            model = getattr(field.queryset, 'model', None)
            if model is not None:
                model_field = model._meta.pk
                if isinstance(model_field, models.AutoField):
                    return {'type': 'string', 'format': 'uid'}
        return super()._map_field(field)

    def custom_map_serializer(self, serializer):
        required = []
        properties = {}

        for field in serializer.fields.values():
            if isinstance(field, serializers.HiddenField):
                continue

            if field.required:
                required.append(field.field_name)

            schema = self.custom_map_field(field)
            if field.read_only:
                schema['readOnly'] = True
            if field.write_only:
                schema['writeOnly'] = True
            if field.allow_null:
                schema['nullable'] = True
            if field.default and field.default != empty:
                schema['default'] = field.default
            if field.help_text:
                schema['description'] = str(field.help_text)
            self.custom_map_field_validators(field, schema)

            properties[field.field_name] = schema

        result = {'properties': properties}
        if len(required) > 0:
            result['required'] = required
        else:
            result['required'] = []

        return result

    def custom_map_field_validators(self, field, schema):
        #:  RegexValidator causes problems generating regex pattern
        #:  remove it for now
        for v in field.validators:
            if isinstance(v, validators.EmailValidator):
                schema['format'] = 'email'
            if isinstance(v, validators.URLValidator):
                schema['format'] = 'uri'
            elif isinstance(v, validators.MaxLengthValidator):
                attr_name = 'maxLength'
                if isinstance(field, serializers.ListField):
                    attr_name = 'maxItems'
                schema[attr_name] = v.limit_value
            elif isinstance(v, validators.MinLengthValidator):
                attr_name = 'minLength'
                if isinstance(field, serializers.ListField):
                    attr_name = 'minItems'
                schema[attr_name] = v.limit_value
            elif isinstance(v, validators.MaxValueValidator):
                schema['maximum'] = v.limit_value
            elif isinstance(v, validators.MinValueValidator):
                schema['minimum'] = v.limit_value
            elif isinstance(v, validators.DecimalValidator):
                if v.decimal_places:
                    schema['multipleOf'] = float(
                        '.' + (v.decimal_places - 1) * '0' + '1'
                    )
                if v.max_digits:
                    digits = v.max_digits
                    if v.decimal_places is not None and v.decimal_places > 0:
                        digits -= v.decimal_places
                    schema['maximum'] = int(digits * '9') + 1
                    schema['minimum'] = -schema['maximum']

    def get_custom_request_body(self, path, method):
        view = self.view

        if method not in ('PUT', 'PATCH', 'POST'):
            return {}

        if not hasattr(view, 'get_serializer'):
            return {}

        try:
            serializer = view.get_serializer()
        except exceptions.APIException:
            serializer = None
            warnings.warn(
                '{}.get_serializer() raised an exception during '
                'schema generation. Serializer fields will not be '
                'generated for {} {}.'.format(
                    view.__class__.__name__, method, path
                )
            )

        if not isinstance(serializer, serializers.Serializer):
            return {}

        content = self.custom_map_serializer(serializer)
        # No required fields for PATCH
        if method == 'PATCH':
            del content['required']
        # No read_only fields for request.
        for name, schema in content['properties'].copy().items():
            if 'readOnly' in schema:
                del content['properties'][name]

        component_name = self.get_component_name(path, serializer, method)
        if component_name not in self.components.keys():
            self.components.update({component_name: content})

        return {
            'content': {
                ct: {
                    'schema': {
                        '$ref': f'#/components/schemas/{component_name}'
                    }
                }
                for ct in self.content_types
            }
        }

    def get_custom_responses(self, path, method):
        resp_dict = CONCRETE_FAIL_RESPONSES.copy()
        if method == 'POST':
            success_status = '201'
            success_description = 'Created'
        elif method == 'DELETE':
            return {'204': {'description': 'No content'}, **resp_dict}
        else:
            success_status = '200'
            success_description = 'Ok'
        content = {}

        if not hasattr(self.view, 'get_serializer'):
            return {'200': {'description': 'Ok', 'content': {}}}
        try:
            serializer = self.view.get_serializer()
        except exceptions.APIException:
            serializer = None
            warnings.warn(
                '{}.get_serializer() raised an exception during '
                'schema generation. Serializer fields will not be '
                'generated for {} {}.'.format(
                    self.view.__class__.__name__, method, path
                )
            )

        if isinstance(serializer, serializers.Serializer):
            content = self.custom_map_serializer(serializer)

            # No write_only fields for response.
            for name, schema in content['properties'].copy().items():
                if 'writeOnly' in schema:
                    del content['properties'][name]
                    content['required'] = [
                        f for f in content['required'] if f != name
                    ]
        item_name = self.get_component_name(path, serializer)
        if item_name not in self.components.keys():
            self.components.update({item_name: content})
        if method != 'GET' or '{uid}' in path:
            component_name = item_name
        else:
            list_name = self.get_component_name(path, serializer, method)
            if list_name not in self.components.keys():
                list_dict = CONCRETE_DEFAULT_LIST_RESP.copy()
                list_dict.update(
                    {
                        'results': {
                            'type': 'array',
                            'items': {
                                '$ref': f'#/components/schemas/{item_name}'
                            },
                        }
                    }
                )
                self.components.update(
                    {list_name: {'properties': list_dict, 'type': 'object'}}
                )
            component_name = list_name

        resp_dict.update(
            {
                success_status: {
                    'description': success_description,
                    'content': {
                        ct: {
                            'schema': {
                                '$ref': f'#/components/schemas/{component_name}'
                            }
                        }
                        for ct in self.content_types
                    },
                }
            }
        )
        return resp_dict

    def get_component_name(self, path, serializer, method=None):
        if method == 'GET' and '{uid}' not in path:
            suffix = 'List'
        else:
            suffix = 'Detail'
        try:
            return f'{suffix}{serializer.Meta.ref_name}'
        except AttributeError:
            try:
                name = serializer.__name__.replace(
                    'ModelSerializer', ''
                ).replace('Serializer', '')
            except Exception:
                name = serializer.__class__.__name__.replace(
                    'ModelSerializer', ''
                ).replace('Serializer', '')
            return f'{suffix}{name}'
