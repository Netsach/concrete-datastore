# coding: utf-8
from __future__ import unicode_literals, absolute_import, print_function
import re


def remove_prefix(value):
    return value.split('.')[1]


def replace_prefix(value):
    return value.replace('.', '_')


def camel_case_to_dash_case(value):
    return re.sub(r'([a-z])([A-Z])', r'\1-\2', value).lower()
