# coding: utf-8


VERSION = (1, 0)


def get_version(version=VERSION):
    return '.'.join(map(str, version))


DEFAULT_API_NAMESPACE = 'api_v1'

__version__ = get_version(VERSION)
