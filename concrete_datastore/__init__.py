# coding: utf-8


VERSION = (0, 1, 0)


def get_version(version=VERSION):
    return '.'.join(map(str, version))


__version__ = get_version(VERSION)
