# coding: utf-8
import os
from concrete_datastore.settings.base import *
from concrete_datastore.settings.utils import load_datamodel
from plugin_concrete_olaf.celery_scheduling_settings import *


PROJECT_ROOT = os.path.dirname(os.path.realpath(__file__)) + '/'
MEDIA_ROOT = os.path.join(PROJECT_ROOT, 'media/')
STATIC_ROOT = os.path.join(PROJECT_ROOT, 'static/')

SITE_ID = 1
INTERNAL_IPS = ['127.0.0.1']
DEBUG = True
ALLOWED_HOSTS = ('*',)
SECRET_KEY = 'development_settings_secret_key'  # nosec

# CREATE USER "user-concrete-datastore" WITH PASSWORD 'pwd-concrete-datastore';
# ALTER USER "user-concrete-datastore" createdb;
# CREATE DATABASE "db-concrete-datastore";
# ALTER DATABASE "db-concrete-datastore" OWNER TO "user-concrete-datastore";
# GRANT ALL PRIVILEGES ON DATABASE "db-concrete-datastore" to "user-concrete-datastore";

POSTGRES_DB = os.environ.get('POSTGRES_DB', 'db-concrete-datastore')

POSTGRES_USER = os.environ.get('POSTGRES_USER', 'user-concrete-datastore')

POSTGRES_PASSWORD = os.environ.get(
    'POSTGRES_PASSWORD', 'pwd-concrete-datastore'
)

POSTGRES_HOST = os.environ.get('POSTGRES_HOST', 'localhost')

POSTGRES_PORT = int(os.environ.get('POSTGRES_PORT', 5432))

DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'NAME': POSTGRES_DB,
        'USER': POSTGRES_USER,
        'PASSWORD': POSTGRES_PASSWORD,
        'HOST': POSTGRES_HOST,
        'PORT': POSTGRES_PORT,
    }
}

MIGRATION_MODULES = {'concrete': 'concrete_datastore.concrete.migrations'}

# Email
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

INSTALLED_APPS += ['debug_toolbar', 'django_filters']

MIDDLEWARE += ['debug_toolbar.middleware.DebugToolbarMiddleware']

SCHEME = "http"
HOSTNAME = "localhost"
PORT = "8000"

META_MODEL_DEFINITIONS = load_datamodel(
    datamodel_path=os.path.join(
        PROJECT_ROOT, 'datamodel/current-datamodel.json'
    )
)

DISABLED_MODELS = ()

EMAIL_HOST = os.environ.get("EMAIL_HOST", '')
EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER", '')
EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD", '')
EMAIL_PORT = os.environ.get("EMAIL_PORT", 587)
EMAIL_USE_TLS = True
EMAIL_USE_SSL = False
EMAIL_TIMEOUT = None
EMAIL_SSL_KEYFILE = None
EMAIL_SSL_CERTFILE = None

DEFAULT_CHARSET = 'utf-8'

ALLOWED_INCLUDE_ROOTS = ()

SERVER_EMAIL = os.environ.get("EMAIL_SENDER", EMAIL_HOST_USER)
EMAIL_REPLY_TO = os.environ.get("EMAIL_REPLY_TO", SERVER_EMAIL)


API_REGISTER_EMAIL_FILTER = r'.*'

USE_TWO_FACTOR_AUTH = False

MFA_RULE_PER_USER = "plugin_concrete_olaf.mfa.mfa_rule.mfa_olaf_rule"

ROOT_URLCONF = "plugin_concrete_olaf.urls"

ENABLE_AUTHENTICATED_USER_THROTTLING = False
ENABLE_ANONYMOUS_USER_THROTTLING = False

SAM_API_TOKEN = "4423ed09d86b754ae3a569b465fc6c6d1d126d73"
SAM_API_URL = "http://preprod-api-sam-database-occam.globecast.nms/api/v1.1/"

POD_API_TOKEN = "21881c5bc361ca1f5e91efa268f73b4d2f2b36e0"
POD_API_URL = "http://localhost:8001/api/v1.1/"

INSTALLED_PLUGINS = {"plugin_concrete_olaf": "1.0.0"}

try:
    import celery_once

    try:
        CELERY_ONCE_TIMEOUT = CELERY_ONCE_TIMEOUT
    except NameError:
        CELERY_ONCE_TIMEOUT = 20 * 60
    ONCE = {
        'backend': 'celery_once.backends.Redis',
        'settings': {
            'url': BROKER_URL,
            'default_timeout': CELERY_ONCE_TIMEOUT,
        },
    }
except ImportError:
    pass

# END of generated settings
