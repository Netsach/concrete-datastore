# coding: utf-8
import os
from concrete_datastore.settings.base import *
from concrete_datastore.settings.utils import load_datamodel

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
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
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

INSTALLED_APPS += [
    'debug_toolbar',
    'django_filters',
    'ns_core.coreApp',
    'test_core.mainApp',
]

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

SERVER_EMAIL = EMAIL_HOST_USER

CELERYBEAT_SCHEDULE['run_resource_watchers'] = {
    'task': 'ns_core.coreApp.automation.periodics.async_run_resource_watchers',
    'schedule': timedelta(seconds=10),
    'options': {'queue': 'run_resource_watchers'},
}

CELERYBEAT_SCHEDULE['run_job_scheduler'] = {
    'task': 'ns_core.coreApp.automation.periodics.async_run_job_scheduler',
    'schedule': timedelta(seconds=10),
    'options': {'queue': 'run_job_scheduler'},
}
CELERYBEAT_SCHEDULE['run_update_workflows'] = {
    'task': 'ns_core.coreApp.automation.periodics.async_run_update_workflows',
    'schedule': timedelta(seconds=10),
    'options': {'queue': 'run_update_workflows'},
}

CELERYBEAT_SCHEDULE['run_checks'] = {
    'task': 'ns_core.coreApp.automation.periodics.async_run_checks',
    'schedule': timedelta(seconds=3600),
    'options': {'queue': 'run_checks'},
}
CELERYBEAT_SCHEDULE['sync_jobs_states']: {
    'task': 'ns_core.coreApp.automation.periodics.async_sync_jobs_states',
    'schedule': timedelta(seconds=1800),
    'options': {'queue': 'sync_jobs_states'},
}

ONCE = {
    'backend': 'celery_once.backends.Redis',
    'settings': {'url': BROKER_URL, 'default_timeout': 60},
}
# INSTALLED_PLUGINS['ns_core'] = '4.4.0'
