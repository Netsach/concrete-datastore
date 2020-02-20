# coding: utf-8
from __future__ import unicode_literals, absolute_import, print_function

from concrete_datastore.parsers.constants import STD_SPECIFIER


def validate_specifier(specifier_dict):
    specifier_type = specifier_dict['std.specifier']
    specifier_keys = STD_SPECIFIER[specifier_type]

    for key in specifier_keys:
        if key not in specifier_dict:
            raise ValueError(f'Missing {key}')
