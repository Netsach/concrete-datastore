# coding: utf-8
ATLEAST_LEVEL_ATTRS = {
    'simpleuser': {'is_active': True},
    'manager': {'is_staff': True},
    'admin': {'admin': True},
    'superuser': {'is_superuser': True},
}

EXACT_LEVEL_ATTRS = {
    'blocked': {
        'is_active': False,
        'is_staff': False,
        'admin': False,
        'is_superuser': False,
    },
    'simpleuser': {
        'is_active': True,
        'is_staff': False,
        'admin': False,
        'is_superuser': False,
    },
    'manager': {
        'is_active': True,
        'is_staff': True,
        'admin': False,
        'is_superuser': False,
    },
    'admin': {
        'is_active': True,
        'is_staff': True,
        'admin': True,
        'is_superuser': False,
    },
    'superuser': {
        'is_active': True,
        'is_staff': True,
        'admin': True,
        'is_superuser': True,
    },
}

CRUD_LEVEL = ["anonymous", "authenticated", "admin", "superuser", "manager"]

LIST_USER_LEVEL = ["blocked", "simpleuser", "manager", "admin", "superuser"]

HANDELED_MODELISATION_VERSIONS = ('1.0.0',)

TYPE_EQ = {
    'ForeignKey': 'fk',
    'ManyToManyField': 'm2m',
    'BooleanField': 'bool',
    'TextField': 'txt',
    'CharField': 'char',
    'URLField': 'url',
    'IntegerField': 'int',
    'FloatField': 'float',
    'DecimalField': 'float',
    'JSONField': 'json',
    'FileField': 'file',
    'ImageField': 'file',
    'DateTimeField': 'datetime',
    'DateField': 'date',
    'BigIntegerField': 'int',
}

EMPTY_VALUES_MAP = {
    'TextField': {'empty_value': '', 'field_type': str},
    'CharField': {'empty_value': '', 'field_type': str},
}
