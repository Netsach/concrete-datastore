# coding: utf-8
import os
import sys


def django():
    CONCRETE_SETTINGS_MODULE = os.environ.get(
        'CONCRETE_SETTINGS', 'development.settings'
    )

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", CONCRETE_SETTINGS_MODULE)

    try:
        from django.core.management import execute_from_command_line
    except ImportError:
        raise ImportError("Could not import Django...")

    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    django()
