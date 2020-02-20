# coding: utf-8


VERSION = (1, 1)


def get_version(version=VERSION):
    return '.'.join(map(str, version))


API_NAMESPACE = 'api_v1_1'

__version__ = get_version(VERSION)
