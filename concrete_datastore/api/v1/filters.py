# coding: utf-8
import uuid
import functools
import re
from django.db.models import Q
from django.contrib.gis.measure import D
from django.contrib.auth import get_user_model
from django_filters.rest_framework import DjangoFilterBackend
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

TYPES_VALUES_MAP = {
    "str": lambda x: x,
    "int": lambda x: int(x),
    "float": lambda x: float(x),
    "bool": lambda x: True if x.lower() == 'true' else False,
    "null": lambda x: None,
}

JSON_FILTER_PATTERN = r'^\"(?P<str>.*)\"$|(?P<int>^\d+$)|(?P<float>^\d+\.\d+([e][+-]?\d+)?$)|(?P<bool>^true$|^false$)|(?P<null>^null$|^none$)'
REGEX_DATETIME_MICROSECOND = "^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{1,6}Z$"
REGEX_DATETIME_SECOND = "^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$"


def cast_value_to_right_type(query_value):
    match = re.search(JSON_FILTER_PATTERN, query_value, flags=re.IGNORECASE)
    if match is None:
        raise ValueError(f'{query_value} is not a valid value')
    match_group = match.groupdict()
    q_type, q_value = next(
        (x, y) for x, y in match_group.items() if y is not None
    )
    return TYPES_VALUES_MAP[q_type](q_value)


def get_filter_field_type(model_class, param) -> str:
    """
    Return the type (as String) of the target field that we want to filter
    """
    splitted_param = param.split('__')
    if (
        model_class._meta.get_field(splitted_param[0]).get_internal_type()
        == 'JSONField'
    ):
        return 'JSONField'
    if len(splitted_param) == 1:
        return model_class._meta.get_field(
            splitted_param[0]
        ).get_internal_type()
    elif len(splitted_param) == 2:
        first_param, second_param = splitted_param
        if (
            model_class._meta.get_field(first_param).get_internal_type()
            != 'ForeignKey'
        ):
            raise ValidationError(
                {
                    "message": (
                        f"{param}: Multi level filters"
                        " available only for foreign keys"
                    )
                }
            )
        return (
            model_class._meta.get_field(first_param)
            .remote_field.model._meta.get_field(second_param)
            .get_internal_type()
        )

    # If we have field__fkfield__fkfieldfkfield or more, raise an error
    # We can at most have field__fkfield as filter
    else:
        raise ValidationError(
            {
                "message": (
                    f"{param}: filter not available for more than 1 level"
                )
            }
        )


def ensure_uuid_valid(value, version=None):
    try:
        uuid.UUID(value, version=version)
    except ValueError:
        return False
    else:
        return True


def convert_type(string, field_type, close_period=True):
    if string == '':
        message = "Attempting to convert an empty string to a date format"
        raise ValidationError({"message": message})
    if field_type == 'DateTimeField':
        # Expected format YYYY-MM-DD HH:MM[:ss[.uuuuuu]][TZ]
        regex_ms = re.compile(REGEX_DATETIME_MICROSECOND)
        regex_second = re.compile(REGEX_DATETIME_SECOND)

        check_microseconds = regex_ms.match(str(string))
        check_seconds = regex_second.match(str(string))

        dt = ensure_pendulum(string)
        #: If the given value contains microseconds,
        #: the method convert_type must return the exact value
        if check_microseconds:
            return format_datetime(dt)

        #: If the given value does not contain microseconds but
        #: conains a datetime, the method convert_type must
        #: either return the `start_of` or `end_of` second, depending
        #: on the argument `close_period`
        #: Otherwise the return value should be the `start_of` or
        #: `end_of` day of the given date.
        #: the variable `time_limit_unit` will contain either
        #: `"second"` or `"day"`
        if check_seconds:
            time_limit_unit = 'second'
        else:
            time_limit_unit = 'day'
        if close_period is True:
            dt = dt.end_of(time_limit_unit)
        else:
            dt = dt.start_of(time_limit_unit)
        return format_datetime(dt)

    if field_type == 'DateField':
        # Expected YYYY-MM-DD
        dt = ensure_pendulum(string)
        # Deactivated by lco, a date is a date, no time in it
        # if close_period:
        #     dt.end_of('day')
        return dt.to_date_string()
    if field_type in ('DecimalField', 'FloatField'):
        return float(string)
    #: Otherwise, the field is an IntegerField
    return int(string)


class CustomShemaOperationParameters:
    def return_if_not_details(self, view, value, extra_condition=True):
        if view.detail is False and extra_condition:
            return value
        return []

    def get_q_objects(self, q_filter, q_exclude, custom_filter, exclude):
        if exclude is False:
            if q_filter is None:
                q_filter = Q(**custom_filter)
            else:
                q_filter &= Q(**custom_filter)
        else:
            if q_exclude is None:
                q_exclude = Q(**custom_filter)
            else:
                q_exclude &= Q(**custom_filter)
        return q_filter, q_exclude

    def get_custom_filtered_queryset(self, qs, q_filter, q_exclude):
        if q_filter is not None:
            qs = qs.filter(q_filter)
        if q_exclude is not None:
            qs = qs.exclude(q_exclude)
        return qs


class ExcludeFilterBackend(DjangoFilterBackend):
    """
    This class inherits form DjangoFilterBackend and uses only negated
    query_parms (only ending with '!')
    The filter method will exclude the result of super().filter_queryset
    The exclusion must be performed on each queryparam
    """

    def get_negated_query_params(self, request, view):
        filterset_fields = getattr(view, 'filterset_fields', ())
        query_params = request.query_params
        return [
            {param[:-1]: value}
            for param, value in query_params.items()
            if param.endswith('!') is True
            and '__' not in param  #: this is handeled by another class
            and '_uid' not in param  #: this is handeled by another class
            and param[:-1] in filterset_fields
        ]

    def filter_queryset(self, request, queryset, view):
        def _get_unitary_filterset_backend(query_param):
            class UnitaryFilterBacked(DjangoFilterBackend):
                def get_filterset_kwargs(self, request, queryset, view):
                    return {
                        'data': query_param,
                        'queryset': queryset,
                        'request': request,
                    }

            return UnitaryFilterBacked().filter_queryset(
                request, queryset, view
            )

        for query_param in self.get_negated_query_params(request, view):
            filtered_qs = _get_unitary_filterset_backend(
                query_param=query_param
            )
            filtered_qs_pks = filtered_qs.values_list('pk', flat=True)
            queryset = queryset.exclude(pk__in=filtered_qs_pks)
        return queryset


class FilterDistanceBackend(BaseFilterBackend, CustomShemaOperationParameters):
    suffixes_map = {
        'gte': (
            'get the values greater than or equal to the given distance '
            '(expected value format: DISTANCE,LONGITUDE,LATITUDE)'
        ),
        'lte': (
            'get the values less than or equal to the given distance '
            '(expected value format: DISTANCE,LONGITUDE,LATITUDE)'
        ),
        'gt': (
            'get the values greater than the given distance '
            '(expected value format: DISTANCE,LONGITUDE,LATITUDE)'
        ),
        'lt': (
            'get the values less than the given distance '
            '(expected value format: DISTANCE,LONGITUDE,LATITUDE)'
        ),
        'range': (
            'get the values between the two given distances (expected '
            'value format: DISTANCE1,DISTANCE2,LONGITUDE,LATITUDE)'
        ),
        'range!': (
            'get the values outside of the two given distances (expected '
            'value format: DISTANCE1,DISTANCE2,LONGITUDE,LATITUDE)'
        ),
    }

    def remove_from_queryset(self, view):
        #: Remove PointField field from filterset_fields because
        #: they cannot be filtered with the other filter backends
        filterset_fields = getattr(view, 'filterset_fields', ())
        new_filterset_fields = tuple(
            filter_field
            for filter_field in filterset_fields
            if (
                get_filter_field_type(view.model_class, filter_field)
                != 'PointField'
            )
        )
        setattr(view, 'filterset_fields', new_filterset_fields)

    def get_schema_operation_parameters(self, view):
        params = []
        for key, description in self.suffixes_map.items():
            params.extend(
                [
                    {
                        'name': f'{field_name}_distance_{key}',
                        'required': False,
                        'in': 'query',
                        'description': description,
                        'schema': {'type': 'string'},
                    }
                    for field_name in getattr(view, 'filterset_fields', ())
                    if get_filter_field_type(view.model_class, field_name)
                    == 'PointField'
                ]
            )

        self.remove_from_queryset(view=view)

        return self.return_if_not_details(view=view, value=params)

    def get_float_or_error(self, value):
        try:
            return float(value)
        except Exception:
            raise ValidationError(f'"{value}" is not a valid float')

    def filter_queryset(self, request, queryset, view):
        # Only applicable on PointField objects
        q_object_filter = None
        q_object_exclude = None
        query_params = request.query_params
        filterset_fields = getattr(view, 'filterset_fields', ())
        for param in query_params:
            exclude = False
            valid_param = any(
                [
                    param.endswith(f'__distance_{lookup}')
                    for lookup in self.suffixes_map.keys()
                ]
            )
            if valid_param is False:
                continue
            param_field, lookup = param.rsplit('__distance_', 1)
            if param_field not in filterset_fields:
                continue
            if (
                get_filter_field_type(queryset.model, param_field)
                != 'PointField'
            ):
                continue
            values = query_params.get(param).split(',')
            comparaison_lookup = lookup in ('lt', 'lte', 'gt', 'gte')
            range_lookup = lookup in ('range', 'range!')
            if comparaison_lookup is True:
                #: If the lookup is one of [lt, lte, gt, gte]
                #: the split should have three elements
                if len(values) != 3:
                    raise ValidationError(
                        f"Distance filter with lookup {lookup} needs the "
                        "following parameters: Distance, longitude and "
                        "latitude"
                    )
                distance = self.get_float_or_error(values[0])
                longitude = self.get_float_or_error(values[1])
                latitude = self.get_float_or_error(values[2])
                point = Point(longitude, latitude)
                custom_filter = {param: (point, D(m=distance))}
            elif range_lookup is True:
                #: If the lookup is one of [range, range!]
                #: the split should have four elements
                if len(values) != 4:
                    raise ValidationError(
                        f"Distance filter with lookup {lookup} needs the "
                        "following parameters: Distance1, Distance2, "
                        "longitude and latitude"
                    )
                distance1 = self.get_float_or_error(values[0])
                distance2 = self.get_float_or_error(values[1])
                min_distance = min(distance1, distance2)
                max_distance = max(distance1, distance2)
                longitude = self.get_float_or_error(values[2])
                latitude = self.get_float_or_error(values[3])
                point = Point(longitude, latitude)
                custom_filter = {
                    '{}__distance_gte'.format(param_field): (
                        point,
                        D(m=min_distance),
                    ),
                    '{}__distance_lte'.format(param_field): (
                        point,
                        D(m=max_distance),
                    ),
                }
                if lookup.endswith('!'):
                    exclude = True
            else:
                raise ValidationError(
                    f"Distance filter with lookup {lookup} is not supported. "
                    f"Supported lookup values are {list(self.suffixes_map)}"
                )

            q_object_filter, q_object_exclude = self.get_q_objects(
                q_filter=q_object_filter,
                q_exclude=q_object_exclude,
                custom_filter=custom_filter,
                exclude=exclude,
            )

        self.remove_from_queryset(view=view)
        return self.get_custom_filtered_queryset(
            qs=queryset, q_filter=q_object_filter, q_exclude=q_object_exclude
        )


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
                'name': 'level!',
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
            {
                'name': 'atleast!',
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
        if 'level!' in query_params:
            return queryset.model.exclude_by_exact_level(
                queryset=queryset, level=query_params.get('level!')
            )
        if 'atleast' in query_params:
            return queryset.model.filter_by_at_least_level(
                queryset=queryset, level=query_params.get('atleast')
            )
        if 'atleast!' in query_params:
            return queryset.model.exclude_by_at_least_level(
                queryset=queryset, level=query_params.get('atleast!')
            )

        return queryset


class FilterSupportingOrBackend(
    BaseFilterBackend, CustomShemaOperationParameters
):
    def get_schema_operation_parameters(self, view):

        params = [
            {
                'name': f'{field_name}__in{neg}',
                'required': False,
                'in': 'query',
                'description': (
                    'List of values separated by comma'
                    f'{" (to exclude)" if neg == "!" else ""}'
                ),
                'schema': {'type': 'string'},
            }
            for field_name in getattr(view, 'filterset_fields', ())
            if get_filter_field_type(view.model_class, field_name)
            != 'ManyToManyField'
            for neg in ('', '!')
        ]
        return self.return_if_not_details(view=view, value=params)

    def filter_queryset(self, request, queryset, view):
        query_params = request.query_params
        filterset_fields = getattr(view, 'filterset_fields', ())

        q_object_filter = None
        q_object_exclude = None
        for param in query_params:
            exclude = False
            bare_param = param
            if param.endswith('!'):
                bare_param = param[:-1]
                exclude = True

            if not bare_param.endswith('__in'):
                continue
            if bare_param.replace('__in', '') not in filterset_fields:
                continue
            values = query_params.get(param).split(',')

            filter_field_type = get_filter_field_type(
                queryset.model, bare_param.replace('__in', '')
            )
            if filter_field_type in (
                'UUIDField',
                'ForeignKey',
                'ManyToManyField',
            ):
                for value in values:
                    if not ensure_uuid_valid(value):
                        message = f"'{value}' is not a valid UUID"
                        raise ValidationError(
                            {"message": (f"{bare_param}: {message}")}
                        )

            if filter_field_type == 'BooleanField':
                if set(values).difference(['True', 'False', 'None']):
                    message = (
                        f"{bare_param}: {values} must contain olny 'True', "
                        "'False' and/or 'None' (case sensitive)"
                    )
                    raise ValidationError({"message": message})
            custom_filter = {bare_param: values}

            q_object_filter, q_object_exclude = self.get_q_objects(
                q_filter=q_object_filter,
                q_exclude=q_object_exclude,
                custom_filter=custom_filter,
                exclude=exclude,
            )

        return self.get_custom_filtered_queryset(
            qs=queryset, q_filter=q_object_filter, q_exclude=q_object_exclude
        )


class FilterJSONFieldsBackend(
    BaseFilterBackend, CustomShemaOperationParameters
):
    def remove_from_queryset(self, view):
        #: Remove JSONField field from filterset_fields because
        #: they cannot be filtered with the other filter backends
        filterset_fields = getattr(view, 'filterset_fields', ())
        new_filterset_fields = tuple(
            filter_field
            for filter_field in filterset_fields
            if (
                get_filter_field_type(view.model_class, filter_field)
                != 'JSONField'
            )
        )
        setattr(view, 'filterset_fields', new_filterset_fields)

    def get_schema_operation_parameters(self, view):
        #: The json filter is generic and has no rules. So it is removed
        #: from the openAPI schema.
        #: In this method we will juste remove the JSON fields from the
        #: filterset_fields of the view and return an empty list

        self.remove_from_queryset(view=view)
        return []

    def filter_queryset(self, request, queryset, view):
        query_params = request.query_params
        filterset_fields = getattr(view, 'filterset_fields', ())

        q_object = None
        self.remove_from_queryset(view=view)
        q_object_filter = None
        q_object_exclude = None
        for param in query_params:
            exclude = False
            bare_param = param
            if param.endswith('!'):
                bare_param = param[:-1]
                exclude = True

            splitted_query_params = bare_param.split('__')
            if len(splitted_query_params) == 1:
                continue
            param_field_name = splitted_query_params[0]

            if param_field_name not in filterset_fields:
                continue
            if (
                get_filter_field_type(queryset.model, param_field_name)
                != 'JSONField'
            ):
                continue

            value = query_params.get(param)
            try:
                custom_filter = {bare_param: cast_value_to_right_type(value)}
            except ValueError as e:
                raise ValidationError({'message': f'"{param}": {e}'})
            q_object_filter, q_object_exclude = self.get_q_objects(
                q_filter=q_object_filter,
                q_exclude=q_object_exclude,
                custom_filter=custom_filter,
                exclude=exclude,
            )
            if q_object is None:
                q_object = Q(**custom_filter)
            else:
                q_object &= Q(**custom_filter)

        return self.get_custom_filtered_queryset(
            qs=queryset, q_filter=q_object_filter, q_exclude=q_object_exclude
        )


class FilterSupportingContainsBackend(
    BaseFilterBackend, CustomShemaOperationParameters
):
    def get_schema_operation_parameters(self, view):
        params = [
            {
                'name': f'{field_name}__contains{neg}',
                'required': False,
                'description': f'String{" (to exclude)" if neg == "!" else ""}',
                'in': 'query',
                'schema': {'type': 'string'},
            }
            for field_name in getattr(view, 'filterset_fields', ())
            if get_filter_field_type(view.model_class, field_name)
            in ('CharField', 'TextField')
            for neg in ('', '!')
        ]
        return self.return_if_not_details(view=view, value=params)

    def filter_queryset(self, request, queryset, view):
        query_params = request.query_params
        filterset_fields = getattr(view, 'filterset_fields', ())

        q_object_filter = None
        q_object_exclude = None
        for param in query_params:
            exclude = False
            bare_param = param
            if param.endswith('!'):
                bare_param = param[:-1]
                exclude = True

            if not bare_param.endswith('__contains'):
                continue
            param_field = bare_param.replace('__contains', '')
            if param_field not in filterset_fields:
                continue
            if not get_filter_field_type(queryset.model, param_field) in (
                'CharField',
                'TextField',
            ):
                continue

            custom_filter = {bare_param: query_params.get(param)}
            q_object_filter, q_object_exclude = self.get_q_objects(
                q_filter=q_object_filter,
                q_exclude=q_object_exclude,
                custom_filter=custom_filter,
                exclude=exclude,
            )

        return self.get_custom_filtered_queryset(
            qs=queryset, q_filter=q_object_filter, q_exclude=q_object_exclude
        )


class FilterSupportingInsensitiveContainsBackend(
    BaseFilterBackend, CustomShemaOperationParameters
):
    def get_schema_operation_parameters(self, view):
        params = [
            {
                'name': f'{field_name}__icontains{neg}',
                'required': False,
                'description': f'String{" (to exclude)" if neg == "!" else ""}',
                'in': 'query',
                'schema': {'type': 'string'},
            }
            for field_name in getattr(view, 'filterset_fields', ())
            if get_filter_field_type(view.model_class, field_name)
            in ('CharField', 'TextField')
            for neg in ('', '!')
        ]
        return self.return_if_not_details(view=view, value=params)

    def filter_queryset(self, request, queryset, view):
        query_params = request.query_params
        filterset_fields = getattr(view, 'filterset_fields', ())

        q_object_filter = None
        q_object_exclude = None
        for param in query_params:
            exclude = False
            bare_param = param
            if param.endswith('!'):
                bare_param = param[:-1]
                exclude = True

            if not bare_param.endswith('__icontains'):
                continue
            param_field = bare_param.replace('__icontains', '')
            if param_field not in filterset_fields:
                continue
            if not get_filter_field_type(queryset.model, param_field) in (
                'CharField',
                'TextField',
            ):
                continue

            custom_filter = {bare_param: query_params.get(param)}

            q_object_filter, q_object_exclude = self.get_q_objects(
                q_filter=q_object_filter,
                q_exclude=q_object_exclude,
                custom_filter=custom_filter,
                exclude=exclude,
            )

        return self.get_custom_filtered_queryset(
            qs=queryset, q_filter=q_object_filter, q_exclude=q_object_exclude
        )


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
            if get_filter_field_type(view.model_class, field_name)
            in ('CharField', 'TextField')
        ]
        return self.return_if_not_details(view=view, value=params)

    def filter_queryset(self, request, queryset, view):
        query_params = request.query_params
        filterset_fields = getattr(view, 'filterset_fields', ())

        q_object_filter = None
        q_object_exclude = None

        for param in query_params:
            exclude = False

            if not param.endswith('__isempty'):
                continue
            if query_params.get(param).lower() == 'false':
                exclude = True
            elif query_params.get(param).lower() != 'true':
                continue
            param = param.replace('__isempty', '')
            if param not in filterset_fields:
                continue
            if get_filter_field_type(queryset.model, param) in (
                'CharField',
                'TextField',
            ):
                custom_filter = {'{}__exact'.format(param): ''}
            else:
                continue
            q_object_filter, q_object_exclude = self.get_q_objects(
                q_filter=q_object_filter,
                q_exclude=q_object_exclude,
                custom_filter=custom_filter,
                exclude=exclude,
            )
        return self.get_custom_filtered_queryset(
            qs=queryset, q_filter=q_object_filter, q_exclude=q_object_exclude
        )


class FilterSupportingRangeBackend(
    BaseFilterBackend, CustomShemaOperationParameters
):
    def get_schema_operation_parameters(self, view):
        params = [
            {
                'name': f'{field_name}__range{neg}',
                'required': False,
                'in': 'query',
                'description': (
                    'A range of values separated by comma'
                    f'{" (to exclude)" if neg == "!" else ""}'
                ),
                'schema': {'type': 'string'},
            }
            for field_name in getattr(view, 'filterset_fields', ())
            + ('creation_date', 'modification_date')
            if get_filter_field_type(view.model_class, field_name)
            in RANGEABLE_TYPES
            for neg in ('', '!')
        ]
        return self.return_if_not_details(view=view, value=params)

    def filter_queryset(self, request, queryset, view):
        query_params = request.query_params
        filterset_fields = getattr(view, 'filterset_fields', ()) + (
            'creation_date',
            'modification_date',
        )

        q_object_filter = None
        q_object_exclude = None

        for param in query_params:
            exclude = False
            bare_param = param
            if param.endswith('!'):
                bare_param = param[:-1]
                exclude = True
            if not param.endswith('__range'):
                continue
            target_field = bare_param.replace('__range', '')
            if target_field not in filterset_fields:
                continue

            target_field_type = get_filter_field_type(
                queryset.model, target_field
            )
            if target_field_type not in RANGEABLE_TYPES:
                continue

            values = query_params.get(param).split(',')

            if len(values) < 2:
                raise ValidationError(
                    {
                        "message": (
                            "A comma is expected in the value of the filter. "
                            "Expected values are '<date1>,<date2>', '<date1>,'"
                            " or ',<date2>'"
                        )
                    }
                )
            if len(values) > 2:
                raise ValidationError(
                    {
                        "message": (
                            'Only two comma-separated values are expected, '
                            f'got {len(values)}: {values}'
                        )
                    }
                )

            range_start, range_end = values

            if range_start == '' and range_end == '':
                continue

            elif range_start != '' and range_end == '':
                param = bare_param.replace('__range', '__gte')
                values = convert_type(
                    range_start, target_field_type, close_period=False
                )

            elif range_start == '' and range_end != '':
                param = bare_param.replace('__range', '__lte')
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
            q_object_filter, q_object_exclude = self.get_q_objects(
                q_filter=q_object_filter,
                q_exclude=q_object_exclude,
                custom_filter=custom_filter,
                exclude=exclude,
            )

        return self.get_custom_filtered_queryset(
            qs=queryset, q_filter=q_object_filter, q_exclude=q_object_exclude
        )


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
                        'description': f'{description}',
                        'schema': {'type': 'string'},
                    }
                    for field_name in getattr(view, 'filterset_fields', ())
                    + ('creation_date', 'modification_date')
                    if get_filter_field_type(view.model_class, field_name)
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
            if param.endswith('__gte'):
                return param.replace('__gte', '')
            if param.endswith('__lte'):
                return param.replace('__lte', '')
            if param.endswith('__gt'):
                return param.replace('__gt', '')
            if param.endswith('__lt'):
                return param.replace('__lt', '')
            return None

        q_object_filter = None

        def get_custom_filters(param):
            target_field = get_param_from_query(param)
            if target_field not in filterset_fields:
                return None

            target_field_type = get_filter_field_type(
                queryset.model, target_field
            )
            if target_field_type not in RANGEABLE_TYPES:
                return None
            close_period = True
            if param.endswith('__lt') or param.endswith('__gte'):
                close_period = False
            value = convert_type(
                query_params.get(param),
                target_field_type,
                close_period=close_period,
            )
            if value is None:
                return None
            return {param: value}

        include_filters = [
            get_custom_filters(qp)
            for qp in query_params
            if get_custom_filters(qp) is not None
        ]
        q_object_filter = functools.reduce(
            lambda a, b: a & Q(**b), include_filters, Q()
        )
        return queryset.filter(q_object_filter)


class FilterSupportingForeignKey(
    BaseFilterBackend, CustomShemaOperationParameters
):
    def get_schema_operation_parameters(self, view):
        params = [
            {
                'name': f'{field_name}_uid{neg}',
                'required': False,
                'in': 'query',
                'description': (
                    f'UID of the FK{" (to exclude)" if neg == "!" else ""}'
                ),
                'schema': {'type': 'string'},
            }
            for field_name in getattr(view, 'filterset_fields', ())
            if get_filter_field_type(view.model_class, field_name)
            == 'ForeignKey'
            for neg in ('', '!')
        ]
        return self.return_if_not_details(view=view, value=params)

    def filter_queryset(self, request, queryset, view):
        query_params = request.query_params
        filterset_fields = getattr(view, 'filterset_fields', ())
        q_object_filter = None
        q_object_exclude = None

        for param in query_params:
            exclude = False
            bare_param = param
            if param.endswith('!'):
                bare_param = param[:-1]
                exclude = True
            if not bare_param.endswith('_uid'):
                continue
            cleaned_param = bare_param.replace('_uid', '')
            if cleaned_param not in filterset_fields:
                continue
            cleaned_param_type = get_filter_field_type(
                queryset.model, cleaned_param
            )
            if not cleaned_param_type == 'ForeignKey':
                continue
            value = query_params.get(param)
            custom_filter = {cleaned_param: value}
            #:  "value" must be a valid UUID4, otherwise raise ValidationError
            #:  raises ValueError if not UUID4
            if not ensure_uuid_valid(value, version=4):
                message = f'{bare_param}: « {value} » is not a valid UUID'
                raise ValidationError({"message": message})
            q_object_filter, q_object_exclude = self.get_q_objects(
                q_filter=q_object_filter,
                q_exclude=q_object_exclude,
                custom_filter=custom_filter,
                exclude=exclude,
            )

        return self.get_custom_filtered_queryset(
            qs=queryset, q_filter=q_object_filter, q_exclude=q_object_exclude
        )


class FilterForeignKeyIsNullBackend(
    BaseFilterBackend, CustomShemaOperationParameters
):
    def get_schema_operation_parameters(self, view):
        params = [
            {
                'name': f'{field_name}__isnull',
                'required': False,
                'in': 'query',
                'schema': {'type': 'boolean'},
            }
            for field_name in getattr(view, 'filterset_fields', ())
            if get_filter_field_type(view.model_class, field_name)
            in ('ForeignKey', 'ManyToManyField')
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
            cleaned_param_type = get_filter_field_type(
                queryset.model, field_name
            )
            if cleaned_param_type in ('ForeignKey', 'ManyToManyField'):
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
                'name': f'{field_name}__in{neg}',
                'required': False,
                'description': 'List of uids separated by comma',
                'in': 'query',
                'schema': {'type': 'string'},
            }
            for field_name in getattr(view, 'filterset_fields', ())
            if get_filter_field_type(view.model_class, field_name)
            == 'ManyToManyField'
            for neg in ('', '!')
        ]
        return self.return_if_not_details(view=view, value=params)

    def filter_queryset(self, request, queryset, view):
        query_params = request.query_params
        filterset_fields = getattr(view, 'filterset_fields', ())
        q_object_filter = None
        q_object_exclude = None

        for param in query_params:
            exclude = False
            bare_param = param
            if param.endswith('!'):
                bare_param = param[:-1]
                exclude = True
            if not bare_param.endswith('__in'):
                continue
            field_name = bare_param.replace('__in', '')
            if field_name not in filterset_fields:
                continue
            cleaned_param_type = get_filter_field_type(
                queryset.model, field_name
            )
            if not cleaned_param_type == 'ManyToManyField':
                continue
            values = set(query_params.get(param).split(','))

            #:  "value" must be a valid UUID4, otherwise raise ValidationError
            for value in values:
                if not ensure_uuid_valid(value, version=4):
                    #:  raises ValueError if not UUID4
                    message = f'{bare_param}: « {value} » is not a valid UUID'
                    raise ValidationError({"message": message})

            custom_filter = {bare_param: values}
            q_object_filter, q_object_exclude = self.get_q_objects(
                q_filter=q_object_filter,
                q_exclude=q_object_exclude,
                custom_filter=custom_filter,
                exclude=exclude,
            )

        return self.get_custom_filtered_queryset(
            qs=queryset, q_filter=q_object_filter, q_exclude=q_object_exclude
        ).distinct()
