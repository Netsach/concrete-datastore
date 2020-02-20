# coding: utf-8
import uuid
import functools

from django.db.models import Q, CharField, TextField, ForeignKey

from rest_framework.exceptions import ValidationError
from rest_framework.filters import BaseFilterBackend

from concrete_datastore.api.v1.datetime import format_datetime, ensure_pendulum

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


class FilterUserByLevel(BaseFilterBackend):
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


class FilterSupportingOrBackend(BaseFilterBackend):
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
            custom_filter = {param: values}
            if q_object is None:
                q_object = Q(**custom_filter)
            else:
                q_object &= Q(**custom_filter)
        if q_object is None:
            return queryset

        return queryset.filter(q_object)


class FilterSupportingContainsBackend(BaseFilterBackend):
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


class FilterSupportingEmptyBackend(BaseFilterBackend):
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


class FilterSupportingRangeBackend(BaseFilterBackend):
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


class FilterSupportingComparaisonBackend(BaseFilterBackend):
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


class FilterSupportingForeignKey(BaseFilterBackend):
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


class FilterForeignKeyIsNullBackend(BaseFilterBackend):
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
            if type(queryset.model._meta.get_field(field_name)) == ForeignKey:
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
