# coding: utf-8
from concrete_datastore.settings.base import *
from concrete_datastore.settings.utils import load_datamodel

SITE_ID = 1
INTERNAL_IPS = ['127.0.0.1']
DEBUG = True
ALLOWED_HOSTS = ('*',)
SECRET_KEY = 'development_settings_secret_key'  # nosec

# CREATE USER "user-concrete-server" WITH PASSWORD 'pwd-concrete-server';
# ALTER USER "user-concrete-server" createdb;
# CREATE DATABASE "db-concrete-server";
# ALTER DATABASE "db-concrete-server" OWNER TO "user-concrete-server";
# GRANT ALL PRIVILEGES ON DATABASE "db-concrete-server" to "user-concrete-server";

POSTGRES_DB = os.environ.get('POSTGRES_DB', 'db-concrete-server-2')

POSTGRES_USER = os.environ.get('POSTGRES_USER', 'user-concrete-server')

POSTGRES_PASSWORD = os.environ.get('POSTGRES_PASSWORD', 'pwd-concrete-server')

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

MEDIA_ROOT = os.path.join(PROJECT_ROOT, 'media/')

# Email
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

INSTALLED_APPS += ['debug_toolbar', 'django_filters']

MIDDLEWARE += ['debug_toolbar.middleware.DebugToolbarMiddleware']

SCHEME = "http"
HOSTNAME = "localhost"
PORT = "8000"

META_MODEL_DEFINITIONS = load_datamodel(
    datamodel_path='datamodel/current-datamodel.json'
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
