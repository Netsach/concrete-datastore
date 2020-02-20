# coding: utf-8
import os
import warnings

from django.utils.deprecation import RemovedInNextVersionWarning

from concrete_datastore.settings.base import *

warnings.filterwarnings(action='error')
warnings.filterwarnings(action='ignore', category=RemovedInNextVersionWarning)
warnings.filterwarnings(action='ignore', category=DeprecationWarning)

SITE_ID = 1
PROXY_ENABLED = False
SECRET_KEY = 'development_settings_secret_key'  # nosec

# Email
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

PASSWORD_HASHERS = ('django.contrib.auth.hashers.MD5PasswordHasher',)

UNITTEST_ENABLED = True
DEBUG = True
TEMPLATE_DEBUG = False
TESTS_IN_PROGRESS = True
MIGRATION_MODULES = {'concrete': 'tests.migrations'}

API_MAX_PAGINATION_SIZE = 10
API_MAX_PAGINATION_SIZE_NESTED = 5
DEFAULT_PAGE_SIZE = 10

USE_CONCRETE_ROLES = False

REST_FRAMEWORK['PAGINATE_BY'] = 10
REST_FRAMEWORK['PAGE_SIZE'] = 10


# if django.db.utils.OperationalError: FATAL:  role "user-concrete-datastore" does not exist
# Open a psql shell and
#  > CREATE USER user-concrete-datastore WITH PASSWORD 'pwd-concrete-datastore';
#  > CREATE DATABASE db-concrete-datastore-2;
#  > GRANT ALL PRIVILEGES ON DATABASE db-concrete-datastore-2 to user-concrete-datastore;
#  > ALTER ROLE user-concrete-datastore CREATEDB;

ADMIN_SHOW_USER_PERMISSIONS = True

POSTGRES_DB = os.environ.get('POSTGRES_DB', 'db-concrete-datastore-2')

POSTGRES_USER = os.environ.get('POSTGRES_USER', 'user-concrete-datastore')

POSTGRES_PASSWORD = os.environ.get('POSTGRES_PASSWORD', 'pwd-concrete-datastore')

POSTGRES_HOST = os.environ.get('POSTGRES_HOST', 'localhost')

POSTGRES_PORT = int(os.environ.get('POSTGRES_PORT', 5432))

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': POSTGRES_DB,
        'USER': POSTGRES_USER,
        'PASSWORD': POSTGRES_PASSWORD,
        'HOST': POSTGRES_HOST,
        'PORT': POSTGRES_PORT,
    }
}

LOGGING['handlers']['console'] = {'class': 'logging.NullHandler'}
LOGGING['handlers']['stream'] = {'class': 'logging.NullHandler'}

SCHEME = "http"
HOSTNAME = "testserver"
PORT = "80"

META_MODEL_DEFINITIONS = (
    {
        "ext.m_search_fields": ["name"],
        "ext.m_filter_fields": ["name"],
        "ext.m_list_display": ["name"],
        "std.verbose_name": "RoleModel",
        "ext.m_unique_together": [],
        "ext.m_creation_minimum_level": "manager",
        "ext.m_is_default_public": False,
        "std.description": "",
        "std.fields": [
            {
                "std.specifier": "Field",
                "ext.f_args": {
                    "default": "",
                    "null": False,
                    "blank": False,
                    "max_length": 255,
                },
                "std.verbose_name": "name",
                "ext.force_nested": False,
                "std.name": "name",
                "std.type": "data",
                "std.description": "name",
                "ext.f_type": "CharField",
            }
        ],
        "std.specifier": "Model",
        "std.verbose_name_plural": "RoleModels",
        "ext.m_delete_minimum_level": "manager",
        "std.name": "RoleModel",
        "ext.m_retrieve_minimum_level": "manager",
        "ext.m_update_minimum_level": "manager",
        "ext.m_unicode": "name",
        "ext.m_export_fields": [],
    },
    {
        "ext.m_search_fields": ["name"],
        "ext.m_filter_fields": ["name"],
        "ext.m_list_display": ["name"],
        "std.verbose_name": "ScopedModel",
        "ext.m_unique_together": [],
        "ext.m_creation_minimum_level": "admin",
        "ext.m_is_default_public": True,
        "std.description": "",
        "std.fields": [
            {
                "std.specifier": "Field",
                "ext.f_args": {
                    "default": "",
                    "null": False,
                    "blank": False,
                    "max_length": 255,
                },
                "std.verbose_name": "name",
                "ext.force_nested": False,
                "std.name": "name",
                "std.type": "data",
                "std.description": "name",
                "ext.f_type": "CharField",
            }
        ],
        "std.specifier": "Model",
        "std.verbose_name_plural": "ScopedModels",
        "ext.m_delete_minimum_level": "superuser",
        "std.name": "ScopedModel",
        "ext.m_retrieve_minimum_level": "authenticated",
        "ext.m_update_minimum_level": "manager",
        "ext.m_unicode": "None",
        "ext.m_export_fields": [],
    },
    {
        "ext.m_search_fields": ["name"],
        "ext.m_filter_fields": ["name"],
        "ext.m_list_display": ["name"],
        "std.verbose_name": "NotScopedModel",
        "ext.m_unique_together": [],
        "ext.m_creation_minimum_level": "admin",
        "ext.m_is_default_public": True,
        "std.description": "",
        "std.fields": [
            {
                "std.specifier": "Field",
                "ext.f_args": {
                    "default": "",
                    "null": False,
                    "blank": False,
                    "max_length": 255,
                },
                "std.verbose_name": "name",
                "ext.force_nested": False,
                "std.name": "name",
                "std.type": "data",
                "std.description": "name",
                "ext.f_type": "CharField",
            }
        ],
        "std.specifier": "Model",
        "std.verbose_name_plural": "NotScopedModels",
        "ext.m_delete_minimum_level": "superuser",
        "std.name": "NotScopedModel",
        "ext.m_retrieve_minimum_level": "authenticated",
        "ext.m_update_minimum_level": "manager",
        "ext.m_unicode": "None",
        "ext.m_export_fields": [],
    },
    {
        "std.name": "Group",
        "std.specifier": "Model",
        "std.verbose_name": "Group",
        "std.verbose_name_plural": "Groups",
        "std.description": "Group",
        "ext.m_unicode": 'name',
        "ext.m_list_display": ['name'],
        "ext.m_search_fields": ['name'],
        "ext.m_filter_fields": [],
        "ext.m_creation_minimum_level": "authenticated",
        "ext.m_retrieve_minimum_level": "authenticated",
        "ext.m_update_minimum_level": "authenticated",
        "ext.m_delete_minimum_level": "authenticated",
        "std.fields": [
            {
                "std.name": "name",
                "std.specifier": "Field",
                "std.verbose_name": "name",
                "std.description": "Name of the group",
                "std.type": "data",
                "ext.f_type": "CharField",
                "ext.f_args": {"max_length": 250},
            },
            {
                "std.name": "members",
                "std.specifier": "Field",
                "std.verbose_name": "members",
                "std.description": "Members of the group",
                "std.type": "rel_iterable",
                "ext.f_type": "ManyToManyField",
                "ext.f_args": {
                    'to': 'concrete.User',
                    'blank': True,
                    'null': True,
                    'related_name': "concrete_groups",
                },
            },
        ],
    },
    {
        "std.name": "UniqueTogetherModel",
        "std.specifier": "Model",
        "std.verbose_name": "UniqueTogetherModel",
        "std.verbose_name_plural": "UniqueTogetherModels",
        "std.description": "UniqueTogetherModel",
        "ext.m_creation_minimum_level": "authenticated",
        "ext.m_retrieve_minimum_level": "authenticated",
        "ext.m_update_minimum_level": "authenticated",
        "ext.m_delete_minimum_level": "authenticated",
        "ext.m_unicode": 'name',
        "ext.m_list_display": [],
        "ext.m_search_fields": [],
        "ext.m_filter_fields": [],
        "ext.m_unique_together": ["name", "field1"],
        "std.fields": [
            {
                "std.name": "name",
                "std.specifier": "Field",
                "std.verbose_name": "Name",
                "std.description": "Name",
                "std.type": "data",
                "ext.f_type": "CharField",
                "ext.f_args": {"max_length": 250},
            },
            {
                "std.name": "field1",
                "std.specifier": "Field",
                "std.verbose_name": "Field1",
                "std.description": "Field1",
                "std.type": "data",
                "ext.f_type": "CharField",
                "ext.f_args": {"max_length": 250},
            },
        ],
    },
    {
        "ext.m_filter_fields": [],
        "ext.m_list_display": ["name"],
        "ext.m_search_fields": [],
        "ext.m_unicode": "name",
        "std.description": "ville",
        "std.fields": [
            {
                "ext.f_args": {"max_length": 250},
                "ext.f_type": "CharField",
                "std.description": "name",
                "std.name": "name",
                "std.specifier": "Field",
                "std.type": "data",
                "std.verbose_name": "name",
            }
        ],
        "std.name": "Village",
        "std.specifier": "Model",
        "std.verbose_name": "ville",
        "std.verbose_name_plural": "ville",
    },
    {
        "ext.m_filter_fields": [],
        "ext.m_list_display": ["name"],
        "ext.m_search_fields": [],
        "ext.m_unicode": "name",
        "std.description": "Fusée",
        "std.fields": [
            {
                "ext.f_args": {"max_length": 250},
                "ext.f_type": "CharField",
                "std.description": "name",
                "std.name": "name",
                "std.specifier": "Field",
                "std.type": "data",
                "std.verbose_name": "name",
            }
        ],
        "std.name": "Fusee",
        "std.specifier": "Model",
        "std.verbose_name": "Fusée",
        "std.verbose_name_plural": "Fusée",
    },
    {
        "ext.m_filter_fields": [],
        "ext.m_list_display": [],
        "ext.m_search_fields": [],
        "ext.m_unicode": "Fusee_Village_NotScopedModel",
        "std.description": "UndividedModel",
        "std.fields": [
            {
                "ext.f_args": {"max_length": 250},
                "ext.f_type": "CharField",
                "std.description": "Cloisonnement",
                "std.name": "Fusee_Village_NotScopedModel",
                "std.specifier": "Field",
                "std.type": "data",
                "std.verbose_name": "Cloisonnement",
            }
        ],
        "std.name": "UndividedModel",
        "std.specifier": "Model",
        "std.verbose_name": "UndividedModel",
        "ext.m_creation_minimum_level": "authenticated",
        "ext.m_retrieve_minimum_level": "authenticated",
        "ext.m_update_minimum_level": "authenticated",
        "ext.m_delete_minimum_level": "authenticated",
        "std.verbose_name_plural": "UndividedModel",
    },
    {
        "std.name": "Entity",
        "std.specifier": "Model",
        "std.verbose_name": "Entity",
        "std.verbose_name_plural": "Entitys",
        "std.description": "Entity",
        "ext.m_creation_minimum_level": "authenticated",
        "ext.m_retrieve_minimum_level": "authenticated",
        "ext.m_update_minimum_level": "authenticated",
        "ext.m_delete_minimum_level": "authenticated",
        "ext.m_list_display": [],
        "ext.m_search_fields": [],
        "ext.m_filter_fields": [],
        "std.fields": [
            {
                "std.specifier": "Field",
                "ext.f_args": {
                    "default": "entity name",
                    "max_length": 250,
                    "blank": False,
                },
                "std.verbose_name": "Nom",
                "ext.force_nested": False,
                "std.name": "name",
                "std.type": "data",
                "std.description": "Nom de l'Entity",
                "ext.f_type": "CharField",
            }
        ],
        "ext.m_unicode": "name",
    },
    {
        "std.name": "User",
        "std.specifier": "Model",
        "std.verbose_name": "User",
        "std.verbose_name_plural": "Users",
        "std.description": "User",
        "ext.m_unicode": 'email',
        "ext.m_creation_minimum_level": "authenticated",
        "ext.m_retrieve_minimum_level": "authenticated",
        "ext.m_update_minimum_level": "authenticated",
        "ext.m_delete_minimum_level": "authenticated",
        "ext.m_list_display": ['first_name', 'last_name'],
        "ext.m_search_fields": ['first_name', 'last_name'],
        "ext.m_filter_fields": [],
        "std.fields": [
            {
                "std.specifier": "Field",
                "ext.f_args": {
                    "default": "",
                    "max_length": 250,
                    "blank": True,
                },
                "std.verbose_name": "Prenom",
                "ext.force_nested": False,
                "std.name": "first_name",
                "std.type": "data",
                "std.description": "Prenom",
                "ext.f_type": "CharField",
            },
            {
                "std.specifier": "Field",
                "ext.f_args": {
                    "default": "",
                    "max_length": 250,
                    "blank": True,
                },
                "std.verbose_name": "Nom",
                "ext.force_nested": False,
                "std.name": "last_name",
                "std.type": "data",
                "std.description": "Nom",
                "ext.f_type": "CharField",
            },
        ],
    },
    # Model Project
    {
        "std.name": "Project",
        "std.specifier": "Model",
        "std.verbose_name": "Project",
        "std.description": "Project",
        "ext.m_unicode": 'name',
        "ext.m_creation_minimum_level": "authenticated",
        "ext.m_update_minimum_level": "authenticated",
        "ext.m_delete_minimum_level": "authenticated",
        "ext.m_retrieve_minimum_level": 'anonymous',
        "ext.m_list_display": ['name', 'archived'],
        "ext.m_search_fields": ['name'],
        "ext.m_filter_fields": ['name', 'archived', 'expected_skills'],
        "std.fields": [
            {
                "std.name": "name",
                "std.specifier": "Field",
                "std.verbose_name": "Name",
                "std.description": "Name of the project",
                "std.type": "data",
                "ext.f_type": "CharField",
                "ext.f_args": {'max_length': 200},
            },
            {
                "std.name": "archived",
                "std.specifier": "Field",
                "std.verbose_name": "Archived",
                "std.description": "Is project archived",
                "std.type": "data",
                "ext.f_type": "BooleanField",
                "ext.f_args": {'default': False, 'blank': True},
            },
            {
                "std.name": "description",
                "std.specifier": "Field",
                "std.verbose_name": "Project descriptions",
                "std.description": "Description of the project",
                "std.type": "data",
                "ext.f_type": "TextField",
                "ext.f_args": {},
            },
            {
                "std.name": "members",
                "std.specifier": "Field",
                "std.verbose_name": "Project members",
                "std.description": "Members of the project",
                "std.type": "rel_iterable",
                "ext.f_type": "ManyToManyField",
                "ext.f_args": {
                    'to': 'concrete.User',
                    'blank': True,
                    'null': True,
                    'related_name': "projects",
                },
            },
            {
                "std.name": "expected_skills",
                "std.specifier": "Field",
                "std.verbose_name": "Expected Skills",
                "std.description": "Expected Skills of the project",
                "std.type": "rel_iterable",
                "ext.f_type": "ManyToManyField",
                "ext.f_args": {
                    'to': 'concrete.ExpectedSkill',
                    'blank': True,
                    'null': True,
                    'related_name': "projects",
                },
            },
            {
                "std.name": "picture",
                "std.specifier": "Field",
                "std.verbose_name": "Project Picture",
                "std.description": "Photo of the project",
                "std.type": "data",
                "ext.f_type": "FileField",
                "ext.f_args": {},
            },
        ],
    },
    {
        "std.name": "Category",
        "std.specifier": "Model",
        "std.verbose_name": "Category",
        "std.verbose_name_plural": "Categories",
        "std.description": "Category",
        "ext.m_unicode": 'name',
        "ext.m_creation_minimum_level": "admin",
        "ext.m_update_minimum_level": "admin",
        "ext.m_delete_minimum_level": "admin",
        "ext.m_retrieve_minimum_level": "authenticated",
        "ext.m_list_display": ['name'],
        "ext.m_search_fields": ['name'],
        "ext.m_filter_fields": ['name'],
        "std.fields": [
            {
                "std.name": "name",
                "std.specifier": "Field",
                "std.verbose_name": "Name",
                "std.description": "Name of the category",
                "std.type": "data",
                "ext.f_type": "CharField",
                "ext.f_args": {'max_length': 50},
            }
        ],
    },
    {
        "std.name": "Crud",
        "std.specifier": "Model",
        "std.verbose_name": "Crud",
        "std.verbose_name_plural": "Crud",
        "std.description": "Crud",
        "ext.m_unicode": 'name',
        "ext.m_creation_minimum_level": "admin",
        "ext.m_retrieve_minimum_level": "admin",
        "ext.m_update_minimum_level": "admin",
        "ext.m_delete_minimum_level": "admin",
        "ext.m_list_display": ['name'],
        "ext.m_search_fields": ['name'],
        "ext.m_filter_fields": ['name'],
        "std.fields": [
            {
                "std.name": "name",
                "std.specifier": "Field",
                "std.verbose_name": "Name",
                "std.description": "Name of the crud",
                "std.type": "data",
                "ext.f_type": "CharField",
                "ext.f_args": {'max_length': 50},
            }
        ],
    },
    {
        "std.name": "JsonField",
        "std.specifier": "Model",
        "std.verbose_name": "Crud",
        "std.verbose_name_plural": "Crud",
        "std.description": "Crud",
        "ext.m_unicode": 'name',
        "ext.m_creation_minimum_level": "authenticated",
        "ext.m_retrieve_minimum_level": "authenticated",
        "ext.m_update_minimum_level": "authenticated",
        "ext.m_delete_minimum_level": "authenticated",
        "ext.m_list_display": ['name'],
        "ext.m_search_fields": ['name'],
        "ext.m_filter_fields": ['name'],
        "std.fields": [
            {
                "std.name": "name",
                "std.specifier": "Field",
                "std.verbose_name": "Name",
                "std.description": "Name of the crud",
                "std.type": "data",
                "ext.f_type": "CharField",
                "ext.f_args": {'max_length': 50},
            },
            {
                "std.name": "json_field",
                "std.specifier": "Field",
                "std.verbose_name": "Name",
                "std.description": "Name of the crud",
                "std.type": "data",
                "ext.f_type": "JSONField",
                "ext.f_args": {'encoder': None},
            },
        ],
    },
    {
        "std.name": "Skill",
        "std.specifier": "Model",
        "std.verbose_name": "Skill",
        "std.description": "Skill",
        "ext.m_creation_minimum_level": "authenticated",
        "ext.m_retrieve_minimum_level": "authenticated",
        "ext.m_update_minimum_level": "authenticated",
        "ext.m_delete_minimum_level": "authenticated",
        "ext.m_unicode": 'name',
        "ext.m_list_display": ['name'],
        "ext.m_search_fields": ['name', 'score'],
        "ext.m_filter_fields": ['name', 'score', 'category'],
        "std.fields": [
            {
                "std.name": "name",
                "std.specifier": "Field",
                "std.verbose_name": "Name",
                "std.description": "Name of the skill",
                "std.type": "data",
                "ext.f_type": "CharField",
                "ext.f_args": {'max_length': 200},
            },
            {
                "std.name": "category",
                "std.specifier": "Field",
                "std.verbose_name": "Skill category",
                "std.description": "Category of the skill",
                "std.type": "rel_single",
                "ext.f_type": "ForeignKey",
                "ext.f_args": {
                    'to': 'concrete.Category',
                    'null': True,
                    'blank': True,
                    'related_name': 'skills',
                },
            },
            {
                "std.name": "score",
                "std.specifier": "Field",
                "std.verbose_name": "Skill score",
                "std.description": "Score of the skill",
                "std.type": "data",
                "ext.f_type": "IntegerField",
                "ext.f_args": {},
            },
            {
                "std.name": "description",
                "std.specifier": "Field",
                "std.verbose_name": "Skill descriptions",
                "std.description": "Description of the skill",
                "std.type": "data",
                "ext.f_type": "TextField",
                "ext.f_args": {},
            },
            {
                "std.name": "user",
                "std.specifier": "Field",
                "std.verbose_name": "User",
                "std.description": "User",
                "std.type": "rel_single",
                "ext.f_type": "ForeignKey",
                "ext.f_args": {
                    'to': 'concrete.User',
                    'null': True,
                    'blank': True,
                    'related_name': "skills",
                },
            },
        ],
    },
    {
        "std.name": "ExpectedSkill",
        "std.specifier": "Model",
        "std.verbose_name": "ExpectedSkill",
        "std.description": "ExpectedSkill",
        "ext.m_creation_minimum_level": "authenticated",
        "ext.m_retrieve_minimum_level": "authenticated",
        "ext.m_update_minimum_level": "authenticated",
        "ext.m_delete_minimum_level": "authenticated",
        "ext.m_unicode": 'name',
        "ext.m_list_display": ['name'],
        "ext.m_search_fields": ['name'],
        "ext.m_filter_fields": ['name'],
        "std.fields": [
            {
                "std.name": "name",
                "std.specifier": "Field",
                "std.verbose_name": "Name",
                "std.description": "Name of the skill",
                "std.type": "data",
                "ext.f_type": "CharField",
                "ext.f_args": {'max_length': 200},
            },
            {
                "std.name": "category",
                "std.specifier": "Field",
                "std.verbose_name": "Skill category",
                "std.description": "Category of the skill",
                "std.type": "rel_single",
                "ext.f_type": "ForeignKey",
                "ext.f_args": {
                    'to': 'concrete.Category',
                    'null': True,
                    'related_name': 'expected_skills',
                },
            },
            {
                "std.name": "score",
                "std.specifier": "Field",
                "std.verbose_name": "Skill score",
                "std.description": "Score of the skill",
                "std.type": "data",
                "ext.f_type": "IntegerField",
                "ext.f_args": {},
            },
            {
                "std.name": "description",
                "std.specifier": "Field",
                "std.verbose_name": "Skill descriptions",
                "std.description": "Description of the skill",
                "std.type": "data",
                "ext.f_type": "TextField",
                "ext.f_args": {},
            },
        ],
    },
    {
        "std.name": "DateUtc",
        "std.specifier": "Model",
        "std.verbose_name": "DateUtc",
        "std.description": "DateUtc",
        "ext.m_creation_minimum_level": "authenticated",
        "ext.m_retrieve_minimum_level": "authenticated",
        "ext.m_update_minimum_level": "authenticated",
        "ext.m_delete_minimum_level": "authenticated",
        "ext.m_unicode": 'date',
        "ext.m_list_display": ['date'],
        "ext.m_search_fields": ['date'],
        "ext.m_filter_fields": ['date', 'datetime'],
        "std.fields": [
            {
                "std.name": "datetime",
                "std.specifier": "Field",
                "std.verbose_name": "Name",
                "std.description": "Name of the skill",
                "std.type": "data",
                "ext.f_type": "DateTimeField",
                "ext.f_args": {'null': True},
            },
            {
                "std.name": "date",
                "std.specifier": "Field",
                "std.verbose_name": "Name",
                "std.description": "Name of the skill",
                "std.type": "data",
                "ext.f_type": "DateField",
                "ext.f_args": {'null': True},
            },
        ],
    },
    {
        "std.name": "TestDataLeak",
        "std.specifier": "Model",
        "std.verbose_name": "TestDataLeak",
        "std.description": "TestDataLeak",
        "ext.m_creation_minimum_level": "authenticated",
        "ext.m_retrieve_minimum_level": "authenticated",
        "ext.m_unicode": 'value',
        "ext.m_list_display": ['value'],
        "ext.m_search_fields": ['value'],
        "ext.m_filter_fields": ['value'],
        "std.fields": [
            {
                "std.name": "value",
                "std.specifier": "Field",
                "std.verbose_name": "Value",
                "std.description": "Arbitrary value",
                "std.type": "data",
                "ext.f_type": "TextField",
                "ext.f_args": {"default": "a value"},
            }
        ],
    },
)


DISABLED_MODELS = ("EntityDividerModel",)
EMAIL_HOST = ''
