# coding: utf-8
import os
import warnings

from django.utils.deprecation import RemovedInNextVersionWarning

from concrete_datastore.settings.base import *
from concrete_datastore.settings.utils import load_datamodel

warnings.filterwarnings(action='error')
warnings.filterwarnings(action='ignore', category=RemovedInNextVersionWarning)
warnings.filterwarnings(action='ignore', category=DeprecationWarning)

SITE_ID = 1
PROXY_ENABLED = False
SECRET_KEY = 'development_settings_secret_key'  # nosec

TEST_ROOT = os.path.dirname(os.path.realpath(__file__)) + '/'

# Email
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

PASSWORD_HASHERS = ('django.contrib.auth.hashers.MD5PasswordHasher',)

ENABLE_AUTHENTICATED_USER_THROTTLING = False
ENABLE_ANONYMOUS_USER_THROTTLING = False
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
#  > CREATE USER "user-concrete-datastore" WITH PASSWORD 'pwd-concrete-datastore';
#  > CREATE DATABASE "db-concrete-datastore";
#  > GRANT ALL PRIVILEGES ON DATABASE "db-concrete-datastore" to "user-concrete-datastore";
#  > ALTER ROLE "user-concrete-datastore" CREATEDB;

ADMIN_SHOW_USER_PERMISSIONS = True

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

LOGGING['handlers']['console'] = {'class': 'logging.NullHandler'}
LOGGING['handlers']['stream'] = {'class': 'logging.NullHandler'}

SCHEME = "http"
HOSTNAME = "testserver"
PORT = "80"

META_MODEL_DEFINITIONS = load_datamodel(
    datamodel_path=os.path.join(TEST_ROOT, 'datamodel/unittest-datamodel.yaml')
)

DISABLED_MODELS = ("EntityDividerModel",)
EMAIL_HOST = ''
API_REGISTER_EMAIL_FILTER = '.*'

ENABLE_USERS_SELF_REGISTER = True
