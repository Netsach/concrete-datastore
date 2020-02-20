# coding: utf-8
from __future__ import unicode_literals, absolute_import, print_function
import json


def parse_json(fd):
    data = json.load(fd)
    return data


def parse_json_file(path):
    with open(path, 'r') as fd:
        return parse_json(fd)
