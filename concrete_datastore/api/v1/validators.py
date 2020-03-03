# coding: utf-8
from concrete_datastore.concrete.constants import EMPTY_VALUES_MAP
from django.core.exceptions import ValidationError


def validate_file(fieldfile_obj):
    if fieldfile_obj.file is None:  # skip-test-coverage
        raise ValidationError("Error : missing file.")


def get_field_validator(field):
    # a field's value is considered INVALID if this field
    # is not allowed to be blank AND the value is empty
    empty_value = EMPTY_VALUES_MAP.get(field.f_type, {}).get(
        'empty_value', None
    )
    field_type = EMPTY_VALUES_MAP.get(field.f_type, {}).get(
        'field_type', lambda x: x
    )

    def validate_field(self, value):
        value_is_empty = field_type(value) == empty_value
        invalid = value_is_empty and not field.f_args.get('blank', False)
        if invalid:
            raise ValidationError('This field may not be blank.')
        return value

    return validate_field


def is_field_required(field):
    #
    #                 default is empty | default not empty
    #                ------------------|-------------------
    # blank is True  |      FALSE      |      FALSE
    # ---------------|-----------------|-------------------
    # blank is False |      TRUE       |      FALSE
    # ---------------|-----------------|-------------------
    blank = field.f_args.get('blank', False)
    if blank is True:
        return False

    # if field has no default value, field is required
    if 'default' not in field.f_args:
        return True

    # if there is no empty possible for the field type, it cannot be missing
    if field.f_type not in EMPTY_VALUES_MAP:
        return True

    default = field.f_args['default']
    empty = EMPTY_VALUES_MAP[field.f_type]['empty_value']

    # Field is required if default is empty
    # For BACKWARD-COMPATIBILITY
    # e.g. field STATUS has a default value, cannot be empty,
    # is not required at creation...
    return default == empty
