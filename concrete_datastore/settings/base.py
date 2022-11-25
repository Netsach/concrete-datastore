# coding: utf-8
import os
from datetime import timedelta
from celery.schedules import crontab
from corsheaders.defaults import default_headers

from concrete_datastore.settings.utils import get_log_path

#: Necessary imports for ldap authentication, should not raise error when imported
try:  # nosec
    import ldap  # pylint: disable=import-error
    from django_auth_ldap.config import *  # pylint: disable=import-error
except Exception:
    pass


ALLOWED_HOSTS = []
PROJECT_ROOT = os.path.dirname(os.path.realpath(__file__)) + '/'
STATIC_ROOT = os.path.join(PROJECT_ROOT, 'static/')
MEDIA_ROOT = os.path.join(PROJECT_ROOT, 'media/')
LANGUAGE_CODE = 'fr-fr'
MEDIA_URL = '/m/'
STATIC_URL = '/s/'


STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
)
PASSWORD_MIN_LENGTH = 4
PASSWORD_MIN_DIGITS = 0
PASSWORD_MIN_LOWER = 0
PASSWORD_MIN_UPPER = 0
PASSWORD_MIN_SPECIAL = 0
SPECIAL_CHARACTERS = "!@#$%%^&*()_+-=[]{}|'\""


LOGIN_REDIRECT_URL = 'index-logged'
SOCIAL_AUTH_RAISE_EXCEPTIONS = False

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'concrete_datastore.concrete.password.PasswordMinLengthValidation'
    },
    {
        'NAME': 'concrete_datastore.concrete.password.PasswordMinDigitsValidation'
    },
    {
        'NAME': 'concrete_datastore.concrete.password.PasswordMinLowerValidation'
    },
    {
        'NAME': 'concrete_datastore.concrete.password.PasswordMinUpperValidation'
    },
    {
        'NAME': 'concrete_datastore.concrete.password.PasswordMinSpecialValidation'
    },
]
DATAMODEL_VERSION = '0.0.0'

ALLOW_MULTIPLE_AUTH_TOKEN_SESSION = True

AUTH_CONFIRM_EMAIL_ENABLE = False
AUTH_CONFIRM_EMAIL_DEFAULT_REDIRECT_TO = 'https://www.netsach.org'

# Since python3.8 bandit changed the way to use the `# nosec` in multiline
# strings: the following is accepted in python versions prior to 3.8, and is
# no longer supported since python 3.8:
#
# MY_CONST = """
# password
# """  # nosec
#
# The new right way to use nosec with multiline since python 3.8 is
#
# MY_CONST = (  # nosec
# """
# password
# """
# )
#
# Doing so, black will format it back to the first way, so we have to disable
# black for the following lines.
# Refer to https://github.com/PyCQA/bandit/issues/658 for more details
# about the issue.

# fmt:off
AUTH_CONFIRM_EMAIL_MESSAGE_BODY = (  # nosec
    """
<html>
<body>
<h3>Welcome to {platform},</h3>

<p>Please confirm your access and your email address : {email} by clicking <a rel="notrack" href='{link}'>here</a>. This email will be used to log in.</p>


<h3>Bienvenue sur {platform},</h3>

<p>Merci de confirmer votre accès et votre adresse email : {email} en cliquant <a rel="notrack" href='{link}'>ici</a>. Cet email sera utilisé pour se connecter.</p>
</body>
</html>
"""
)

SECURE_TOKEN_MESSAGE_BODY = (  # nosec
    """
<html>
<body>
<h3>Welcome to {platform},</h3>

<p>Please click <a rel="notrack" href='{link}'>here</a> to authenticate to the platform.</p>


<h3>Bienvenue sur {platform},</h3>

<p>Veuillez cliquer <a rel="notrack" href='{link}'>ici</a> pour vous connecter sur la plateforme.</p>
</body>
</html>
"""
)

SECURE_CONNECT_CODE_MESSAGE_BODY = (  # nosec
    """
<html>
<body>
<h3>Welcome to {platform},</h3>
<p>Please enter the following confirmation code to authenticate to the platform: <br>
<strong>{auth_code}</strong><br>
This code is valid for {min_validity} minutes.
</p>

<h3>Bienvenue sur {platform},</h3>
<p>Veuillez entrer le code de confirmation suivant pour vous connecter sur la plateforme: <br>
<strong>{auth_code}</strong><br>
Ce code est valable pendant {min_validity} minutes.
</p>

</body>
</html>
"""
)

AUTH_CONFIRM_RESET_PASSWORD_EMAIL_BODY = (  # nosec
    """
<html>
<body>
<h3>Reset password</h3>
<p>Please follow <a rel="notrack" href="{link}">this link</a> to reset your password.<br>
Ignore this email if you didn't ask to reset your password.</p><br>

<h3>Mise à jour du mot de passe</h3>
<p>Veuillez suivre <a rel="notrack" href="{link}">ce lien</a> pour mettre à jour votre mot de passe<br>
Veuillez ignorer ce mail si vous n'avez pas demandé à mettre à jour votre mot de passe</p>
</body>
</html>
"""
)


TWO_FACTOR_TOKEN_MSG = (  # nosec
    """
<html>
<body>
<h3>Verification code - {platform_name}</h3>
<p>Please enter the following confirmation code to authenticate to the platform: <br>
<strong>{confirm_code}</strong><br>
This code is valid for {min_validity} minutes.
</p>

<h3>Code de vérification - {platform_name}</h3>
<p>Veuillez entrer le code de confirmation suivant pour vous connecter sur la plateforme: <br>
<strong>{confirm_code}</strong><br>
Ce code est valable pendant {min_validity} minutes.
</p>
</body>
</html>
"""
)

DEFAULT_REGISTER_EMAIL_FORMAT = (  # nosec
    """
<html>
<body>
<h3>Set your password</h3>
<p>Please follow <a rel="notrack" href="{link}">this link</a> to set your password and complete your register process.<p><br>

<h3>Sélectionner votre mot de passe</h3>
<p>Veuillez suivre <a rel="notrack" href="{link}">ce lien</a> pour choisir votre mot de passe et compléter votre inscription.</p><br>
</body>
</html>
"""
)

CREATE_SUPERUSER_EMAIL_MESSAGE_BODY = (  # nosec
    '''
Welcome to Concrete <a href="{admin_url}">{hostname}</a><br>
<br>
You have created a new superuser.
You can now connect to your concrete instance with the following
credentials :<br>

email {email}<br>
password {password}<br>
<br>
Please change your password as you connect for the first time.

'''
)

RESET_PASSWORD_EMAIL_MESSAGE_BODY = (  # nosec
    '''
Welcome to Concrete <a href="{admin_url}">{hostname}</a><br>
<br>
You have requested a new password.
You can now connect to your concrete instance with the following
credentials :<br>
email {email}<br>
password {password}<br>
<br>
Please change your password as you connect for the first time.
'''
)

SEND_OTP_CONFIGURE_LINK = (  # nosec
    '''
You requested to activate the MFA with OTP for your account on {platform}.
<br>
Please reach the following link to configure you favorite OTP application :
<br>
{link}
'''
)


# fmt:on


PASSWORD_CHANGE_TOKEN_EXPIRY_HOURS = 4
SECURE_CONNECT_TOKEN_EXPIRY_TIME_SECONDS = 2 * 3600 * 24  # 2 days
MAX_SECURE_CONNECT_TOKENS = 10

# Secure connect with code
SECURE_CONNECT_CODE_EXPIRY_TIME_SECONDS = 60 * 10  # 10 minutes
SECURE_CONNECT_CODE_LENGTH = 8
MAX_SIMULTANEOUS_SECURE_CONNECT_CODES_PER_USER = 10


DEFAULT_RESET_PASSWORD_URL_FORMAT = (
    '/#/reset-password/{token}/{email}/'  # nosec
)


PLATFORM_NAME = 'Concrete Datastore'

AUTHENTICATION_BACKENDS = [
    'concrete_datastore.authentication.auth.ConcreteBackend',
    'concrete_datastore.authentication.oauth2_utils.NetsachGitLabOAuth2',
]

CONCRETE_REGISTER_BACKENDS = []

MINIMUM_BACKEND_AUTH_LEVEL = 'is_superuser'
MINIMUM_LEVEL_FOR_USER_LIST = 'is_at_least_staff'

ROOT_URLCONF = 'concrete_datastore.routes.urls'

PASSWORD_EXPIRY_TIME = 0  # in days, 0 for no expiration


API_TOKEN_EXPIRY = 0  # in minutes, 0 for no expiration
EXPIRY_EXTRA_PERIOD = 0  # in minutes, 0 for no extra period

CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_HEADERS = default_headers + (
    'Access-Control-Allow-Headers',
    'Access-Control-Allow-Origin',
    'X-CSRFToken',
    'Authorization',
    'X-Entity-Uid',
    'Content-Type',
    'Cache-Control',
)
CORS_ALLOWED_ORIGINS = []

MIDDLEWARE = [
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'social_django.middleware.SocialAuthExceptionMiddleware',
    'concrete_datastore.authentication.oauth2_utils.SocialCustomAuthExceptionMiddleware',
    'concrete_datastore.concrete.middleware.OTPCustomMiddleware',
]

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': (
            os.path.join(os.path.dirname(__file__), "templates"),
            os.path.join(
                os.path.dirname(os.path.dirname(__file__)), "doc/templates"
            ),
            os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                "concrete/templates",
            ),
        ),
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.contrib.auth.context_processors.auth',
                'django.template.context_processors.debug',
                'django.template.context_processors.i18n',
                'django.template.context_processors.media',
                'django.template.context_processors.static',
                'django.template.context_processors.tz',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.request',
                'social_django.context_processors.backends',
                'social_django.context_processors.login_redirect',
            ]
        },
    }
]


TIME_ZONE = 'UTC'
LANGUAGE_CODE = 'en-en'

USE_I18N = True

USE_L10N = True

USE_TZ = True

API_MAX_PAGINATION_SIZE = 250
API_MAX_PAGINATION_SIZE_NESTED = 125
DEFAULT_PAGE_SIZE = 250

# DRF
REST_FRAMEWORK = {
    'DEFAULT_SCHEMA_CLASS': 'concrete_datastore.interfaces.openapi_schema_generator.AutoSchema',
    'DATETIME_FORMAT': "%Y-%m-%dT%H:%M:%SZ",
    'COERCE_DECIMAL_TO_STRING': False,
    'PAGE_SIZE': DEFAULT_PAGE_SIZE,
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework.authentication.BasicAuthentication',
        'rest_framework.authentication.SessionAuthentication',
        'concrete_datastore.api.v1.authentication.TokenExpiryAuthentication',
        'concrete_datastore.api.v1.authentication.URLTokenExpiryAuthentication',
    ),
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.LimitOffsetPagination',
    'DEFAULT_RENDERER_CLASSES': (
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
    ),
    'DEFAULT_THROTTLE_CLASSES': (
        'concrete_datastore.api.v1.throttling.CustomAnonymousRateThrottle',
        'concrete_datastore.api.v1.throttling.CustomUserRateThrottle',
    ),
}

#: Throttling rate should be (requests / duration)
#: Accepted durations are all the strings that start with
#: - "s" (seconds) example: s, sec, second, seconds, ...
#: - "m" (minutes) example: m, min, minute, minutes, ...
#: - "h" (hours) example: h, hou, hour, hours, ...
#: - "d" (days) example: d, day, days, ...
#: Please refer to the implementation of the method for more info
#: https://github.com/encode/django-rest-framework/blob/3.10.2/rest_framework/throttling.py#L106
ENABLE_AUTHENTICATED_USER_THROTTLING = True
USER_THROTTLING_RATE = '500/m'
ENABLE_ANONYMOUS_USER_THROTTLING = True
ANONYMOUS_THROTTLING_RATE = '6/m'

AUTH_USER_MODEL = 'concrete.User'

API_REGISTER_EMAIL_FILTER = r'$^'

ADMIN_SHOW_USER_PERMISSIONS = False

ADMIN_HEADER = "Concrete Backoffice"

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    'django_extensions',
    'social_django',
    'django_otp',
    'rest_framework',
    'rest_framework_gis',
    'django.contrib.gis',
    'corsheaders',
    'concrete_datastore.concrete',
]

LICENSE = 'GNU GENERAL PUBLIC LICENSE Version 3'

OPENAPI_SPEC_TITLE = os.environ.get('APP_INSTANCE', 'Concrete Datastore')

DEFAULT_LOGGING_FORMAT = (
    "%(asctime)s § %(levelname)5s [%(name)s] : %(message)s "
    "([%(filename)s:%(lineno)s %(funcName)s)"
)
DEFAULT_LOGGING_LEVEL = "INFO"

LOGGING_FORMAT = os.environ.get('LOGGING_FORMAT', DEFAULT_LOGGING_FORMAT)
LOGGING_LEVEL = os.environ.get('LOGGING_LEVEL', DEFAULT_LOGGING_LEVEL).upper()

LOGGING = {
    'version': 1,
    'datefmt': "YY-MM-DD HH:mm:ss",
    'formatters': {'verbose': {'format': DEFAULT_LOGGING_FORMAT}},
    'filters': {
        'require_debug_true': {'()': 'django.utils.log.RequireDebugTrue'}
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'filters': ['require_debug_true'],
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'stream': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'safe_file': {
            'level': 'INFO',
            'class': 'logging.handlers.WatchedFileHandler',
            'filename': get_log_path('read.log'),
        },
        'unsafe_file': {
            'level': 'INFO',
            'class': 'logging.handlers.WatchedFileHandler',
            'filename': get_log_path('action.log'),
        },
        'auth_file': {
            'level': 'INFO',
            'class': 'logging.handlers.WatchedFileHandler',
            'filename': get_log_path('auth.log'),
        },
        'celery_file': {
            'level': 'INFO',
            'class': 'logging.handlers.TimedRotatingFileHandler',
            'filename': get_log_path('celery_scheduling.log'),
            'when': 'd',
            'interval': 1,
            'backupCount': 1,
            'formatter': 'verbose',
        },
    },
    'loggers': {
        '': {
            'handlers': ['console', 'stream'],
            'propagate': True,
            'level': 'INFO',
        },
        'concrete_datastore': {
            'handlers': ['console', 'stream'],
            'propagate': False,
            'level': 'DEBUG',
        },
        'django.db.backends': {
            'handlers': ['console', 'stream'],
            'propagate': False,
            'level': 'WARNING',
        },
        'django.request': {
            'handlers': ['console', 'stream'],
            'propagate': False,
            'level': 'WARNING',
        },
        'celery.task': {
            'handlers': ['console', 'stream'],
            'propagate': False,
            'level': 'WARNING',
        },
        'celery.app.trace': {
            'handlers': ['celery_file'],
            'propagate': False,
            'level': 'INFO',
        },
        'celery.worker': {
            'handlers': ['celery_file'],
            'propagate': False,
            'level': 'INFO',
        },
        'api_safe_log': {
            'handlers': ['safe_file'],
            'propagate': True,
            'level': 'INFO',
        },
        'api_unsafe_log': {
            'handlers': ['unsafe_file'],
            'propagate': True,
            'level': 'INFO',
        },
        'api_auth_log': {
            'handlers': ['auth_file'],
            'propagate': True,
            'level': 'INFO',
        },
    },
}
# Dict:
# Key: Task path; Value: Queue name
PLUGINS_TASKS_FUNC = {
    # 'concrete_datastore.dummy_plugin.automation.tasks.dummy_task': 'default_queue',
}


EMAIL_CSS = ''
EMAIL_SENDER_NAME = '<Concrete Datastore>'
EMAIL_HOST = ''
EMAIL_REPLY_TO = ''

# Limit of different values before deactivating filter
LIMIT_DEACTIVATE_FILTER_IN_ADMIN = 50

BROKER_URL = os.environ.get('BROKER_URL', 'redis://localhost:6379/0')
PLUGIN_TASK_TIMEDELTA_SEC = int(
    os.environ.get('PLUGIN_TASK_TIMEDELTA_SEC', 20)
)
BROKER_TRANSPORT_OPTIONS = {
    'fanout_prefix': True,
    'fanout_patterns': True,
    'visibility_timeout': 24 * 60 * 60,
}

INSTALLED_PLUGINS = {
    # 'plugin_concrete_xxx': '1.0.0'
}

CELERYBEAT_SCHEDULE = {
    'async_run_plugin_tasks': {
        'task': 'concrete_datastore.concrete.automation.tasks.async_run_plugin_tasks',
        'schedule': timedelta(seconds=PLUGIN_TASK_TIMEDELTA_SEC),
        'options': {'queue': 'periodic'},
    }
}

USE_CONCRETE_ROLES = False
USE_CORE_AUTOMATION = False
# Example:
# CONCRETE_SCOPES_FILTER_LOOKUP_FOR_UNSUBSCRIBE_JSON = '{"archived": false}'
CONCRETE_SCOPES_FILTER_LOOKUP_FOR_UNSUBSCRIBE_JSON = '{}'
# Populate the Django user from the LDAP directory.
AUTH_LDAP_USER_ATTR_MAP = {
    'email': 'mail',
    "first_name": "givenName",
    "last_name": "sn",
}
AUTH_LDAP_USER_QUERY_FIELD = 'email'

AUTH_LDAP_BIND_AS_AUTHENTICATING_USER = True

# This is the default, but I like to be explicit.
AUTH_LDAP_ALWAYS_UPDATE_USER = True

# Use LDAP group membership to calculate group permissions.
AUTH_LDAP_FIND_GROUP_PERMS = False

# Cache distinguished names and group memberships for an hour to minimize
# LDAP traffic.
AUTH_LDAP_CACHE_TIMEOUT = 3600
USE_AUTH_LDAP = False


SOCIAL_AUTH_GITLAB_KEY = ''
SOCIAL_AUTH_GITLAB_SECRET = ''  # nosec

USE_MULTIPLE_TOKENS = False
# If true, return a new token at each login

SESSIONS_NUMBER_CONTROL_ENABLED = False
# Is used only if USE_MULTIPLE_TOKENS == True

MAX_SIMULTANEOUS_SESSIONS = 1
# 0 for unlimited, only if SESSIONS_NUMBER_CONTROL_ENABLED == True

TWO_FACTOR_CODE_TIMEOUT_SECONDS = 600

USE_TWO_FACTOR_AUTH = False
MFA_RULE_PER_USER = 'concrete_datastore.api.v1.authentication.default_mfa_rule'

SESSION_CONTROL_DEFAULT_RULE = (
    'concrete_datastore.api.v1.serializers.default_session_control_exempt_rule'
)

# Remote concrete authentication
REMOTE_CONCRETE_AUTH_ENABLED = False
URL_REMOTE_DATASTORE = 'http://xxx:8000/api/v1.1/'
AUTH_REMOTE_URI = 'auth/login/'
USERNAME_AUTH_KEY = 'email'

# Backend login group creation rule
BACKEND_GROUP_CREATION_RULE = 'concrete_datastore.api.v1.authentication.default_backend_group_creation_rule'

ALLOW_SEND_EMAIL_ON_REGISTER = True

REGISTER_EMAIL_SUBJECT = "Account created"

DEFAULT_REGISTER_URL_FORMAT = '/#/set-password/{token}/{email}/'  # nosec


# Flag to allow a user to reuse a password on change, only applicable if
# current password is not expired
ALLOW_REUSE_PASSWORD_ON_CHANGE = False

IGNORED_MODELS_ON_DELETE = [
    "DeletedModel",
    "AuthToken",
    "TemporaryToken",
    "SecureConnectToken",
]
ADMIN_URL_ENABLED = True
ADMIN_ROOT_URI = "concrete-datastore-admin"

RETRYING_DELAY_SECONDS = 5

MAX_RETRIES = 10

SMTP_MAILING_USE_ASYNC = False

RETRY_ON_SENDING_SYNC_EMAILS = False

ENABLE_SWAGGER_UI = True

ENABLE_SERVE_DATAMODEL = True
SWAGGER_SPEC_PATH = 'openapi-schema'
SWAGGER_UI_PATH = 'swagger-ui'

ENABLE_USERS_SELF_REGISTER = False

DEFAULT_AUTO_FIELD = 'django.db.models.AutoField'

#: This controls the rate of throttling. The sequence of 1, 2, 4, 8… seconds
#: is multiplied by this factor to define the delay imposed after 1, 2, 3, 4…
#: successive failures. Set to 0 to disable throttling completely.
OTP_TOTP_THROTTLE_FACTOR = 1

#: The number of time steps in the past or future to allow. This will allow the
#: use of expired token(s). Set to 0 to reject expired tokens
OTP_TOTP_TOLERANCE = 1

#: The TOTP issuer used for the QR-Code. Leave to None to use the same value
#: as PLATFORM_NAME
OTP_TOTP_ISSUER = None
