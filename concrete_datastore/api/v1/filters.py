# coding: utf-8
import uuid
import functools

from django.db.models import Q, CharField, TextField, ForeignKey, BooleanField
from django.contrib.gis.db.models import PointField
from django.contrib.gis.measure import D
from django.db.models.fields.related import ManyToManyField
from django.contrib.auth import get_user_model
from rest_framework.exceptions import ValidationError
from rest_framework.filters import BaseFilterBackend
from concrete_datastore.api.v1.datetime import format_datetime, ensure_pendulum
from django.contrib.gis.geos import Point

# target_field type is date or datetime or int or float
RANGEABLE_TYPES = (
    'DateTimeField',
    'DateField',
    'DecimalField',
    'IntegerField',
    'FloatField',
)


def convert_type(string, field_type, close_period=True):
    if string == '':
        raise ValidationError(
            {
                "message": "Attempting to convert an empty string to a date format"
            }
        )
    if field_type in ('DateTimeField', 'DateField'):
        if field_type == 'DateTimeField':
            # Expected format YYYY-MM-DD HH:MM[:ss[.uuuuuu]][TZ]
            dt = ensure_pendulum(string)
            if close_period:
                dt.end_of('day')
            else:
                dt.start_of('day')
            return format_datetime(dt)
        if field_type == 'DateField':
            # Expected YYYY-MM-DD
            dt = ensure_pendulum(string)
            # Deactivated by lco, a date is a date, no time in it
            # if close_period:
            #     dt.end_of('day')
            return dt.to_date_string()
    elif field_type in ('DecimalField', 'FloatField'):
        return float(string)
    else:
        return int(string)


class CustomShemaOperationParameters:
    def return_if_not_details(self, view, value, extra_condition=True):
        if view.detail is False and extra_condition:
            return value
        return []


class FilterDistanceBackend(BaseFilterBackend, CustomShemaOperationParameters):
    def remove_from_queryset(self, view):
        #: Remove PointField field from filterset_fields because
        #: they cannot be filtered with the other filter backends
        filterset_fields = getattr(view, 'filterset_fields', ())
        new_filterset_fields = tuple(
            filter_field
            for filter_field in filterset_fields
            if (
                view.model_class._meta.get_field(
                    filter_field
                ).get_internal_type()
                != 'PointField'
            )
        )
        setattr(view, 'filterset_fields', new_filterset_fields)

    def get_schema_operation_parameters(self, view):
        params = [
            {
                'name': f'{field_name}__distance',
                'required': False,
                'in': 'query',
                'description': 'DISTANCE,LONGITUDE,LATITUDE',
                'schema': {'type': 'string'},
            }
            for field_name in getattr(view, 'filterset_fields', ())
            if view.model_class._meta.get_field(field_name).get_internal_type()
            == 'PointField'
        ]
        self.remove_from_queryset(view=view)
        return self.return_if_not_details(view=view, value=params)

    def filter_queryset(self, request, queryset, view):
        # Only applicable on PointField objects
        #: The filter is __distance=XXX,LONGITUDE,LATITUDE
        q_object = None
        query_params = request.query_params
        filterset_fields = getattr(view, 'filterset_fields', ())
        for param in query_params:
            if not param.endswith('__distance'):
                continue
            param_field = param.replace('__distance', '')
            if param_field not in filterset_fields:
                continue
            if (
                queryset.model._meta.get_field(param_field).get_internal_type()
                != 'PointField'
            ):
                continue
            #: The split should have three elements
            values = query_params.get(param).split(',')
            if len(values) != 3:
                raise ValidationError(
                    "Distance filter needs the following parameters: "
                    "Distance, longitude and latitude."
                )
            distance = int(values[0])
            longitude = float(values[1])
            latitude = float(values[2])

            point = Point(longitude, latitude)
            custom_filter = {
                '{}__distance_lte'.format(param_field): (point, D(m=distance))
            }
            if q_object is None:
                q_object = Q(**custom_filter)
            else:
                q_object &= Q(**custom_filter)

        self.remove_from_queryset(view=view)
        if q_object is None:
            return queryset

        return queryset.filter(q_object)


class FilterUserByLevel(BaseFilterBackend, CustomShemaOperationParameters):
    def get_schema_operation_parameters(self, view):
        params = [
            {
                'name': 'level',
                'required': False,
                'in': 'query',
                'schema': {'type': 'string'},
            },
            {
                'name': 'atleast',
                'required': False,
                'in': 'query',
                'schema': {'type': 'string'},
            },
        ]
        return self.return_if_not_details(
            view=view,
            value=params,
            extra_condition=view.model_class == get_user_model(),
        )

    def filter_queryset(self, request, queryset, view):
        # Only appyable on user models
        if view.basename.lower() != 'user':
            return queryset

        query_params = request.query_params
        if 'level' in query_params:
            return queryset.model.filter_by_exact_level(
                queryset=queryset, level=query_params.get('level')
            )
        if 'atleast' in query_params:
            return queryset.model.filter_by_at_least_level(
                queryset=queryset, level=query_params.get('atleast')
            )

        return queryset


class FilterSupportingOrBackend(
    BaseFilterBackend, CustomShemaOperationParameters
):
    def get_schema_operation_parameters(self, view):
        params = [
            {
                'name': f'{field_name}__in',
                'required': False,
                'in': 'query',
                'description': 'List of values separated by comma',
                'schema': {'type': 'string'},
            }
            for field_name in getattr(view, 'filterset_fields', ())
            if type(view.model_class._meta.get_field(field_name))
            != ManyToManyField
        ]
        return self.return_if_not_details(view=view, value=params)

    def filter_queryset(self, request, queryset, view):
        query_params = request.query_params
        filterset_fields = getattr(view, 'filterset_fields', ())

        q_object = None
        for param in query_params:
            if not param.endswith('__in'):
                continue
            if param.replace('__in', '') not in filterset_fields:
                continue

            values = query_params.get(param).split(',')
            if isinstance(
                queryset.model._meta.get_field(param.replace('__in', '')),
                BooleanField,
            ):
                if set(values).difference(['True', 'False', 'None']):
                    raise ValidationError(
                        {
                            "message": (
                                f"{param}: {values} must contain olny 'True', "
                                "'False' and/or 'None' (case sensitive)"
                            )
                        }
                    )
            custom_filter = {param: values}
            if q_object is None:
                q_object = Q(**custom_filter)
            else:
                q_object &= Q(**custom_filter)
        if q_object is None:
            return queryset

        return queryset.filter(q_object)


class FilterSupportingContainsBackend(
    BaseFilterBackend, CustomShemaOperationParameters
):
    def get_schema_operation_parameters(self, view):
        params = [
            {
                'name': f'{field_name}__contains',
                'required': False,
                'in': 'query',
                'schema': {'type': 'string'},
            }
            for field_name in getattr(view, 'filterset_fields', ())
            if isinstance(
                view.model_class._meta.get_field(field_name),
                (CharField, TextField),
            )
        ]
        return self.return_if_not_details(view=view, value=params)

    def filter_queryset(self, request, queryset, view):
        query_params = request.query_params
        filterset_fields = getattr(view, 'filterset_fields', ())

        q_object = None
        for param in query_params:
            if not param.endswith('__contains'):
                continue
            param_field = param.replace('__contains', '')
            if param_field not in filterset_fields:
                continue
            if not isinstance(
                queryset.model._meta.get_field(param_field),
                (CharField, TextField),
            ):
                continue

            custom_filter = {param: query_params.get(param)}
            if q_object is None:
                q_object = Q(**custom_filter)
            else:
                q_object &= Q(**custom_filter)
        if q_object is None:
            return queryset

        return queryset.filter(q_object)


class FilterSupportingEmptyBackend(
    BaseFilterBackend, CustomShemaOperationParameters
):
    def get_schema_operation_parameters(self, view):
        params = [
            {
                'name': f'{field_name}__isempty',
                'required': False,
                'in': 'query',
                'description': 'True or False',
                'schema': {'type': 'boolean'},
            }
            for field_name in getattr(view, 'filterset_fields', ())
            if isinstance(
                view.model_class._meta.get_field(field_name),
                (CharField, TextField),
            )
        ]
        return self.return_if_not_details(view=view, value=params)

    def filter_queryset(self, request, queryset, view):
        query_params = request.query_params
        filterset_fields = getattr(view, 'filterset_fields', ())

        q_object = None
        for param in query_params:
            if not param.endswith('__isempty'):
                continue
            if query_params.get(param) != 'true':
                continue
            param = param.replace('__isempty', '')
            if param not in filterset_fields:
                continue
            if isinstance(
                queryset.model._meta.get_field(param), (CharField, TextField)
            ):
                custom_filter = {'{}__exact'.format(param): ''}
            else:
                continue

            if q_object is None:
                q_object = Q(**custom_filter)
            else:
                q_object &= Q(**custom_filter)
        if q_object is None:
            return queryset

        return queryset.filter(q_object)


class FilterSupportingRangeBackend(
    BaseFilterBackend, CustomShemaOperationParameters
):
    def get_schema_operation_parameters(self, view):
        params = [
            {
                'name': f'{field_name}__range',
                'required': False,
                'in': 'query',
                'description': 'A range of values separated by comma',
                'schema': {'type': 'string'},
            }
            for field_name in getattr(view, 'filterset_fields', ())
            + ('creation_date', 'modification_date')
            if view.model_class._meta.get_field(field_name).get_internal_type()
            in RANGEABLE_TYPES
        ]
        return self.return_if_not_details(view=view, value=params)

    def filter_queryset(self, request, queryset, view):
        query_params = request.query_params
        filterset_fields = getattr(view, 'filterset_fields', ()) + (
            'creation_date',
            'modification_date',
        )

        q_object = None
        for param in query_params:
            if not param.endswith('__range'):
                continue
            target_field = param.replace('__range', '')
            if target_field not in filterset_fields:
                continue

            target_field_type = queryset.model._meta.get_field(
                target_field
            ).get_internal_type()
            if target_field_type not in RANGEABLE_TYPES:
                continue

            values = query_params.get(param).split(',')
            correct_range_values = len(values) == 2

            if not correct_range_values:
                continue

            range_start, range_end = values

            if range_start == '' and range_end == '':
                continue

            elif range_start != '' and range_end == '':
                param = param.replace('__range', '__gte')
                values = convert_type(
                    range_start, target_field_type, close_period=False
                )

            elif range_start == '' and range_end != '':
                param = param.replace('__range', '__lte')
                values = convert_type(
                    range_end, target_field_type, close_period=True
                )

            else:
                values = (
                    convert_type(
                        range_start, target_field_type, close_period=False
                    ),
                    convert_type(
                        range_end, target_field_type, close_period=True
                    ),
                )

            custom_filter = {param: values}
            if q_object is None:
                q_object = Q(**custom_filter)
            else:
                q_object &= Q(**custom_filter)

        if q_object is None:
            return queryset

        return queryset.filter(q_object)


class FilterSupportingComparaisonBackend(
    BaseFilterBackend, CustomShemaOperationParameters
):
    def get_schema_operation_parameters(self, view):
        suffixes_map = {
            'gte': 'get the values greater than or equal to a given value',
            'lte': 'get the values less than or equal to a given value',
            'gt': 'get the values greater than to a given value',
            'lt': 'get the values less than to a given value',
        }
        params = []
        for key, description in suffixes_map.items():
            params.extend(
                [
                    {
                        'name': f'{field_name}__{key}',
                        'required': False,
                        'in': 'query',
                        'description': description,
                        'schema': {'type': 'string'},
                    }
                    for field_name in getattr(view, 'filterset_fields', ())
                    + ('creation_date', 'modification_date')
                    if view.model_class._meta.get_field(
                        field_name
                    ).get_internal_type()
                    in RANGEABLE_TYPES
                ]
            )
        return self.return_if_not_details(view=view, value=params)

    def filter_queryset(self, request, queryset, view):
        query_params = request.query_params
        filterset_fields = getattr(view, 'filterset_fields', ()) + (
            'creation_date',
            'modification_date',
        )

        def get_param_from_query(param):
            target_field = param
            if target_field.endswith('__gte'):
                return target_field.replace('__gte', '')
            if target_field.endswith('__lte'):
                return target_field.replace('__lte', '')
            if target_field.endswith('__gt'):
                return target_field.replace('__gt', '')
            if target_field.endswith('__lt'):
                return target_field.replace('__lt', '')
            return None

        q_object = None

        def get_custom_filters(param):
            target_field = get_param_from_query(param)
            if target_field not in filterset_fields:
                return None

            target_field_type = queryset.model._meta.get_field(
                target_field
            ).get_internal_type()
            if target_field_type not in RANGEABLE_TYPES:
                return None
            value = convert_type(query_params.get(param), target_field_type)
            if value is None:
                return None
            return {param: value}

        filters = [
            get_custom_filters(qp)
            for qp in query_params
            if get_custom_filters(qp) is not None
        ]
        if len(filters) == 0:
            return queryset
        q_object = functools.reduce(lambda a, b: a & Q(**b), filters, Q())

        return queryset.filter(q_object)


class FilterSupportingForeignKey(
    BaseFilterBackend, CustomShemaOperationParameters
):
    def get_schema_operation_parameters(self, view):
        params = [
            {
                'name': f'{field_name}_uid',
                'required': False,
                'in': 'query',
                'description': 'UID of the FK',
                'schema': {'type': 'string'},
            }
            for field_name in getattr(view, 'filterset_fields', ())
            if type(view.model_class._meta.get_field(field_name)) == ForeignKey
        ]
        return self.return_if_not_details(view=view, value=params)

    def filter_queryset(self, request, queryset, view):
        query_params = request.query_params
        filterset_fields = getattr(view, 'filterset_fields', ())
        q_object = None
        for param in query_params:
            if not param.endswith('_uid'):
                continue
            cleaned_param = param.replace('_uid', '')
            if cleaned_param not in filterset_fields:
                continue
            cleaned_param_type = queryset.model._meta.get_field(cleaned_param)
            if not type(cleaned_param_type) == ForeignKey:
                continue
            value = query_params.get(param)
            custom_filter = {cleaned_param: value}
            #:  "value" must be a valid UUID4, otherwise raise ValidationError
            try:
                #:  raises ValueError if not UUID4
                uuid.UUID(value, version=4)
            except ValueError:
                raise ValidationError(
                    {"message": f'{param}: « {value} » is not a valid UUID'}
                )

            if q_object is None:
                q_object = Q(**custom_filter)
            else:
                q_object &= Q(**custom_filter)
        if q_object is None:
            return queryset

        return queryset.filter(q_object)


class FilterForeignKeyIsNullBackend(
    BaseFilterBackend, CustomShemaOperationParameters
):
    def get_schema_operation_parameters(self, view):
        params = [
            {
                'name': f'{field_name}__isull',
                'required': False,
                'in': 'query',
                'schema': {'type': 'boolean'},
            }
            for field_name in getattr(view, 'filterset_fields', ())
            if type(view.model_class._meta.get_field(field_name))
            in (ForeignKey, ManyToManyField)
        ]
        return self.return_if_not_details(view=view, value=params)

    def filter_queryset(self, request, queryset, view):
        query_params = request.query_params
        filterset_fields = getattr(view, 'filterset_fields', ())

        q_object = None
        for param in query_params:
            if not param.endswith('__isnull'):
                continue
            if query_params.get(param) not in ['true', 'false']:
                continue
            field_name = param.replace('__isnull', '')
            if field_name not in filterset_fields:
                continue
            param_value = True if query_params.get(param) == 'true' else False
            cleaned_param_type = queryset.model._meta.get_field(field_name)
            if type(cleaned_param_type) in (ForeignKey, ManyToManyField):
                custom_filter = {param: param_value}
            else:
                continue

            if q_object is None:
                q_object = Q(**custom_filter)
            else:
                q_object &= Q(**custom_filter)
        if q_object is None:
            return queryset

        return queryset.filter(q_object)


class FilterSupportingManyToMany(
    BaseFilterBackend, CustomShemaOperationParameters
):
    def get_schema_operation_parameters(self, view):
        params = [
            {
                'name': f'{field_name}__in',
                'required': False,
                'description': 'List of uids separated by comma',
                'in': 'query',
                'schema': {'type': 'string'},
            }
            for field_name in getattr(view, 'filterset_fields', ())
            if type(view.model_class._meta.get_field(field_name))
            == ManyToManyField
        ]
        return self.return_if_not_details(view=view, value=params)

    def filter_queryset(self, request, queryset, view):
        query_params = request.query_params
        filterset_fields = getattr(view, 'filterset_fields', ())
        q_object = None
        for param in query_params:
            if not param.endswith('__in'):
                continue
            field_name = param.replace('__in', '')
            if field_name not in filterset_fields:
                continue
            cleaned_param_type = queryset.model._meta.get_field(field_name)
            if not type(cleaned_param_type) == ManyToManyField:
                continue
            values = set(query_params.get(param).split(','))

            #:  "value" must be a valid UUID4, otherwise raise ValidationError
            for value in values:
                try:
                    #:  raises ValueError if not UUID4
                    uuid.UUID(value, version=4)
                except ValueError:
                    raise ValidationError(
                        {
                            "message": f'{param}: « {value} » is not a valid UUID'
                        }
                    )

            custom_filter = {param: values}
            if q_object is None:
                q_object = Q(**custom_filter)
            else:
                q_object &= Q(**custom_filter)
        if q_object is None:
            return queryset

        return queryset.filter(q_object).distinct()
