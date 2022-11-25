# coding: utf-8


VERSION = (1, 51, 0)


def get_version(version=VERSION):
    return '.'.join(map(str, version))


__version__ = get_version(VERSION)
