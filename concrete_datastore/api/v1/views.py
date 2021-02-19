# coding: utf-8
import pendulum
import logging
import decimal
import uuid
import sys
import re
import os
from urllib.parse import urljoin, unquote, urlparse, urlunparse
from importlib import import_module
from itertools import chain
from datetime import date

from django_filters.rest_framework import DjangoFilterBackend
from django.contrib.auth.models import AnonymousUser
from django.db.models.deletion import ProtectedError
from django.core.exceptions import (
    PermissionDenied,
    ObjectDoesNotExist,
    SuspiciousOperation,
)
from django.contrib.gis.db.models import (
    PointField,
)  # it includes all default fields

from django.contrib.auth import authenticate, get_user_model
from django.http.request import QueryDict
from django.utils import timezone
from django.apps import apps
from django.conf import settings
from rest_framework_gis.filters import DistanceToPointFilter
from rest_framework.decorators import action
from rest_framework.utils.urls import remove_query_param, replace_query_param
from rest_framework.response import Response
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.reverse import reverse
from rest_framework.status import (
    HTTP_400_BAD_REQUEST,
    HTTP_429_TOO_MANY_REQUESTS,
    HTTP_201_CREATED,
    HTTP_403_FORBIDDEN,
    HTTP_401_UNAUTHORIZED,
    HTTP_200_OK,
    HTTP_412_PRECONDITION_FAILED,
    HTTP_204_NO_CONTENT,
)
from rest_framework import authentication, permissions, generics, viewsets

from concrete_datastore.concrete.models import (  # pylint:disable=E0611
    AuthToken,
    DeletedModel,
    DIVIDER_MODEL,
    UNDIVIDED_MODEL,
    PasswordChangeToken,
    Email,
    SecureConnectToken,
)
from concrete_datastore.api.v1.permissions import (
    UserAccessPermission,
    filter_queryset_by_permissions,
    filter_queryset_by_divider,
)
from concrete_datastore.api.v1.pagination import ExtendedPagination
from concrete_datastore.api.v1.serializers import (
    AuthLoginSerializer,
    UserSerializer,
    RegisterSerializer,
    ChangePasswordSerializer,
    ResetPasswordSerializer,
    make_account_me_serialier,
    ConcretePasswordValidator,
    make_serializer_class,
    SecureLoginSerializer,
)
from concrete_datastore.api.v1.filters import (
    FilterSupportingOrBackend,
    FilterSupportingEmptyBackend,
    FilterSupportingContainsBackend,
    FilterSupportingRangeBackend,
    FilterUserByLevel,
    FilterSupportingComparaisonBackend,
    FilterForeignKeyIsNullBackend,
    FilterSupportingForeignKey,
    FilterSupportingManyToMany,
    FilterDistanceBackend,
)

from concrete_datastore.api.v1.authentication import (
    TokenExpiryAuthentication,
    expire_secure_token,
    URLTokenExpiryAuthentication,
)
from concrete_datastore.concrete.automation.signals import user_logged_in
from concrete_datastore.concrete.meta import list_of_meta
from concrete_datastore.concrete.meta import meta_models, meta_registered
from concrete_datastore.api.v1 import DEFAULT_API_NAMESPACE
from concrete_datastore.api.v1.exceptions import (
    PasswordInsecureValidationError,
    WrongEntityUIDError,
)
from concrete_datastore.interfaces.csv import csv_streaming_response


UserModel = get_user_model()

logger = logging.getLogger('concrete-datastore')
logger_api_safe = logging.getLogger('api_safe_log')
logger_api_unsafe = logging.getLogger('api_unsafe_log')
logger_api_auth = logging.getLogger('api_auth_log')

main_app = apps.get_app_config('concrete')

URL_TIMESTAMP = (
    '(?:'
    '\/'
    'timestamp_start:(?P<timestamp_start>\d+\.\d+)'
    '(?:-timestamp_end:(?P<timestamp_end>\d+\.\d+))?'
    '\/?'
    ')?'
)


def get_client_ip(request):
    if 'HTTP_X_FORWARDED_FOR' in request.META:
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def parse_to_float(query_param):
    if query_param is None or query_param == 'None':
        return 0.0

    if type(query_param) in (str,):
        try:
            return float(query_param.replace('/', ''))
        except ValueError:
            logger.info(
                'Unable to convert {}: {} to float'.format(
                    query_param, type(query_param)
                )
            )
            return 0.0

    if type(query_param) in (int, decimal.Decimal):
        return float(query_param)

    if type(query_param) in (float,):
        return query_param

    raise ValueError('Unable to convert {} to float'.format(type(query_param)))


def remove_instances_user_tracked_fields(instance, removed_dividers_pks=None):
    if not removed_dividers_pks:
        return

    divider_related_models = [
        'EntityDividerModel',
        'UndividedModel',
        'DefaultDivider',
        'User',
        DIVIDER_MODEL,
    ]
    models_names = []
    for model in meta_models:
        model_name = model.get_model_name()
        if (
            model_name not in divider_related_models
            and model_name not in UNDIVIDED_MODEL
        ):
            models_names.append(model_name)

    _filter = {'{}__in'.format(DIVIDER_MODEL.lower()): removed_dividers_pks}
    for model in models_names:
        c_model = apps.get_model('concrete.{}'.format(model))
        instances = c_model.objects.filter(**_filter)
        can_view_instances = instances.filter(can_view_users__pk=instance.pk)
        can_admin_instances = instances.filter(can_admin_users__pk=instance.pk)
        for i in can_view_instances:
            i.can_view_users.remove(instance.pk)
        for i in can_admin_instances:
            i.can_admin_users.remove(instance.pk)


def validate_request_permissions(request):
    minimum_retrieve_level = settings.MINIMUM_LEVEL_FOR_USER_LIST
    user_has_permission = False

    user_has_permission = getattr(request.user, minimum_retrieve_level, False)
    if user_has_permission is False:
        raise PermissionDenied('User has not the permission to list')


def apply_filter_since(queryset, timestamp_start, timestamp_end=None):
    """
    timestamp_start: float
    timestamp_end: float
    """
    if timestamp_end is None:
        pendulum_instance = pendulum.instance(timezone.now())
        timestamp_end = pendulum_instance.timestamp()  # pylint:disable=E1102

    queryset = queryset.filter(
        modification_date__range=(
            pendulum.from_timestamp(parse_to_float(timestamp_start)),
            pendulum.from_timestamp(parse_to_float(timestamp_end)),
        )
    )
    return queryset, timestamp_end


class SecurityRulesMixin(object):
    def options(self, request, *args, **kwargs):
        default_options = super().options(request, *args, **kwargs).data
        default_options['rules'] = []
        for validator in settings.AUTH_PASSWORD_VALIDATORS:
            module_name, validator_name = validator['NAME'].rsplit('.', 1)
            module = import_module(module_name)
            validator = getattr(module, validator_name)()
            default_options['rules'].append(
                {
                    'message_en': validator.get_help_text(),
                    'message_fr': validator.get_help_text_fr(),
                    'code': validator.code,
                }
            )
        return Response(data=default_options, status=HTTP_200_OK)


class RetrieveSecureTokenApiView(generics.GenericAPIView):
    """
    This view is used to create a secure token and send an email to the user
    """

    serializer_class = ResetPasswordSerializer

    def post(self, request, *args, **kwargs):
        # The ResetPasswordSerializer only need an email like this view
        serializer = ResetPasswordSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                data={
                    "message": serializer.errors,
                    "_errors": ["INVALID_DATA"],
                },
                status=HTTP_400_BAD_REQUEST,
            )

        email = serializer.validated_data["email"].lower()

        user_queryset = UserModel.objects.filter(email=email, is_active=True)
        if not user_queryset.exists():
            return Response(
                data={
                    "message": "Wrong email address",
                    "_errors": ["WRONG_EMAIL_ADDRESS"],
                },
                status=HTTP_400_BAD_REQUEST,
            )

        user = user_queryset.first()
        # Check if the secure token is expired and expire in database
        secure_tokens = SecureConnectToken.objects.filter(
            user=user, expired=False
        )
        for secure_token in secure_tokens:
            expire_secure_token(secure_token)
        secure_tokens_count = secure_tokens.count()
        if secure_tokens_count >= settings.MAX_SECURE_CONNECT_TOKENS:
            return Response(status=HTTP_429_TOO_MANY_REQUESTS)
        token = SecureConnectToken.objects.create(user=user)
        token.url = os.path.join(
            request.META.get('HTTP_REFERER', '/'),
            '#',
            'secure-connect/login/{}'.format(token.value),
        )
        token.save()

        if token.mail_sent is False:
            token.send_mail()
        data = {'message': 'Token created and email sent'}
        return Response(data=data, status=HTTP_201_CREATED)


class GenerateSecureTokenApiView(generics.GenericAPIView):
    """
    This view is used to create a secure token and send it to a super user
    """

    serializer_class = ResetPasswordSerializer

    def post(self, request, *args, **kwargs):
        # The ResetPasswordSerializer only need an email like this view
        user = self.request.user
        superuser = user.is_superuser is True

        if not superuser:
            return Response(status=HTTP_403_FORBIDDEN)

        serializer = ResetPasswordSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                data={
                    "message": serializer.errors,
                    "_errors": ["INVALID_DATA"],
                },
                status=HTTP_400_BAD_REQUEST,
            )

        email = serializer.validated_data["email"].lower()

        user_queryset = UserModel.objects.filter(email=email, is_active=True)
        if not user_queryset.exists():
            return Response(
                data={
                    "message": "Wrong email address",
                    "_errors": ["WRONG_EMAIL_ADDRESS"],
                },
                status=HTTP_400_BAD_REQUEST,
            )

        user = user_queryset.first()
        # Check if the secure token is expired and expire in database
        secure_tokens = SecureConnectToken.objects.filter(
            user=user, expired=False
        )
        for secure_token in secure_tokens:
            expire_secure_token(secure_token)
        secure_tokens_count = secure_tokens.count()
        if secure_tokens_count >= settings.MAX_SECURE_CONNECT_TOKENS:
            return Response(status=HTTP_429_TOO_MANY_REQUESTS)
        token = SecureConnectToken.objects.create(user=user)

        data = {'secure-token': str(token.value)}
        return Response(data=data, status=HTTP_201_CREATED)


class SecureLoginApiView(generics.GenericAPIView):
    """this view is used to login the user with Secure Login"""

    serializer_class = SecureLoginSerializer
    api_namespace = DEFAULT_API_NAMESPACE

    def __init__(self, api_namespace, *args, **kwargs):
        self.api_namespace = api_namespace
        super().__init__(*args, **kwargs)

    def post(self, request, *args, **kwargs):
        serializer = SecureLoginSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                data={
                    "message": serializer.errors,
                    "_errors": ["INVALID_DATA"],
                },
                status=HTTP_400_BAD_REQUEST,
            )
        token = serializer.validated_data['token']
        try:
            secure_connect_token = SecureConnectToken.objects.get(value=token)
        except ObjectDoesNotExist:
            return Response(
                data={
                    'message': 'Invalid token',
                    "_errors": ["INVALID_TOKEN"],
                },
                status=HTTP_401_UNAUTHORIZED,
            )
        user = secure_connect_token.user

        if expire_secure_token(secure_connect_token):
            return Response(
                data={
                    "message": "Token has expired",
                    "_errors": ["TOKEN_HAS_EXPIRED"],
                },
                status=HTTP_403_FORBIDDEN,
            )

        serializer = UserSerializer(
            instance=user, api_namespace=self.api_namespace
        )
        return Response(data=serializer.data, status=HTTP_200_OK)


class LoginApiView(generics.GenericAPIView):
    """this view is used to login the user"""

    #: Serializer
    serializer_class = AuthLoginSerializer
    api_namespace = DEFAULT_API_NAMESPACE

    def __init__(self, api_namespace, *args, **kwargs):
        self.api_namespace = api_namespace
        super().__init__(*args, **kwargs)

    def post(self, request, *args, **kwargs):
        """
        :param request: needs fields **email** & **password**
        :return:
          return the UserSerializer data (email, url, first_name,
          last_name, level, password and token)
        """

        serializer = AuthLoginSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                data={
                    'message': serializer.errors,
                    "_errors": ["INVALID_DATA"],
                },
                status=HTTP_400_BAD_REQUEST,
            )

        email = serializer.validated_data["email"].lower()

        ip = get_client_ip(request)
        now = pendulum.now('utc').format(settings.LOGGING['datefmt'])
        user = self.request.user
        base_message = f"[{now}|{ip}|{user}|AUTH] "
        # If the remote auth is disabled, do additional checks
        if getattr(settings, 'REMOTE_CONCRETE_AUTH_ENABLED', False) is False:
            try:
                user = UserModel.objects.get(email=email.lower())
            except ObjectDoesNotExist:
                log_request = (
                    base_message
                    + f"Connection attempt to unknown user {email}"
                )
                logger_api_auth.info(log_request)
                return Response(
                    data={
                        'message': 'Wrong auth credentials',
                        "_errors": ["WRONG_AUTH_CREDENTIALS"],
                    },
                    status=HTTP_401_UNAUTHORIZED,
                )
            if user.level == 'blocked':
                log_request = (
                    base_message
                    + f"Connection attempt to blocked user {email}"
                )
                logger_api_auth.info(log_request)
                return Response(
                    data={
                        'message': 'User blocked',
                        "_errors": ["USER_BLOCKED"],
                    },
                    status=HTTP_401_UNAUTHORIZED,
                )

        user = authenticate(
            username=email,
            password=serializer.validated_data["password"],
            from_api=True,
        )
        if user is None:
            log_request = (
                base_message
                + f"Connection attempt to {email} with wrong password"
            )
            logger_api_auth.info(log_request)
            return Response(
                data={
                    'message': 'Wrong auth credentials',
                    "_errors": ["WRONG_AUTH_CREDENTIALS"],
                },
                status=HTTP_401_UNAUTHORIZED,
            )

        if not user.is_confirmed():

            log_request = (
                base_message
                + f"Connection attempt to a not validated user {email}"
            )
            logger_api_auth.info(log_request)
            return Response(
                data={
                    'message': 'Email has not been validated',
                    "_errors": ["EMAIL_NOT_VALIDATED"],
                },
                status=HTTP_412_PRECONDITION_FAILED,
            )

        user_logged_in.send(sender=UserModel, user=user)

        if user.password_has_expired:
            log_request = (
                base_message
                + f"Connection attempt to user {email}, but password is expired"
            )
            logger_api_auth.info(log_request)
            pwd_change_token = PasswordChangeToken.objects.create(user=user)
            return Response(
                data={
                    'message_en': 'Warning! Password has expired',
                    'message_fr': 'Attention ! Votre mot de passe a expiré',
                    "_errors": ["EXPIRED_PASSWORD"],
                    'email': user.email,
                    'password_change_token': str(pwd_change_token.uid),
                },
                status=HTTP_403_FORBIDDEN,
            )

        # Delete existing token for this user
        if settings.ALLOW_MULTIPLE_AUTH_TOKEN_SESSION is False:
            AuthToken.objects.filter(user_id=user.uid).delete()

        UserModel.objects.filter(pk=user.pk).update(last_login=timezone.now())
        module_name, func_name = settings.MFA_RULE_PER_USER.rsplit('.', 1)
        module = import_module(module_name)
        use_mfa_rule = getattr(module, func_name)
        if use_mfa_rule(user=user):
            email_device = user.emaildevice_set.filter(confirmed=True).first()
            if not email_device:
                email_device = user.emaildevice_set.create(
                    email=user.email, name='User default email', confirmed=True
                )
            email_device.generate_challenge()
            serializer = UserSerializer(
                instance=user,
                api_namespace=self.api_namespace,
                context={'is_verified': False},
            )
            logger_api_auth.info(
                base_message + f"Send MFA code to user {user.email}"
            )
            return Response(data=serializer.data, status=HTTP_200_OK)

        serializer = UserSerializer(
            instance=user, api_namespace=self.api_namespace
        )

        log_request = (
            base_message + f"Connection attempt to user {email} is successful"
        )
        logger_api_auth.info(log_request)
        return Response(data=serializer.data, status=HTTP_200_OK)


class ChangePasswordView(SecurityRulesMixin, generics.GenericAPIView):
    """this view is used to change the password for a user"""

    #: Serializer
    serializer_class = ChangePasswordSerializer
    api_namespace = DEFAULT_API_NAMESPACE

    def __init__(self, api_namespace, *args, **kwargs):
        self.api_namespace = api_namespace
        super().__init__(*args, **kwargs)

    def set_password_and_return_resp(self, user, password):
        user.set_password(password)
        user.password_modification_date = date.today()
        user.save()

        return Response(
            data={'email': user.email, 'message': 'Password updated !'},
            status=HTTP_200_OK,
        )

    def change_password_with_token(self, token, user, password):
        #:  Check that PasswordChangeToken exists
        request_token_qs = PasswordChangeToken.objects.filter(uid=token)
        if not request_token_qs.exists():
            return Response(
                data={
                    'message': 'invalid token',
                    "_errors": ["INVALID_TOKEN"],
                },
                status=HTTP_400_BAD_REQUEST,
            )

        #:  Check that PasswordChangeToken belongs to the user
        request_token = request_token_qs.first()
        if user != request_token.user:
            return Response(
                data={
                    'message': 'invalid token',
                    "_errors": ["INVALID_TOKEN"],
                },
                status=HTTP_400_BAD_REQUEST,
            )

        #:  Check that token has not expired
        now = pendulum.now('utc')
        token_too_old = now >= request_token.expiry_date
        if token_too_old:
            request_token.delete()
            return Response(
                data={
                    'message': 'invalid token',
                    "_errors": ["INVALID_TOKEN"],
                },
                status=HTTP_400_BAD_REQUEST,
            )

        #:  Check that new password is different from old one
        if (
            user.password_has_expired
            or not settings.ALLOW_REUSE_PASSWORD_ON_CHANGE
        ):
            same_password = user.check_password(password)
            if same_password:
                return Response(
                    data={
                        'message': 'New password must be different',
                        "_errors": ["CANNOT_USE_SAME_PASSWORD"],
                    },
                    status=HTTP_400_BAD_REQUEST,
                )

        user.set_password(password)
        user.password_modification_date = date.today()
        user.save()
        request_token.delete()

        resp_serializer = UserSerializer(
            instance=user, api_namespace=self.api_namespace
        )

        return Response(data=resp_serializer.data, status=HTTP_200_OK)

    def change_another_user_password(self, target_user, password):
        #:  Check that new password is different from old one
        if (
            target_user.password_has_expired
            or not settings.ALLOW_REUSE_PASSWORD_ON_CHANGE
        ):
            same_password = target_user.check_password(password)
            if same_password:
                return Response(
                    data={
                        'message': 'New password must be different',
                        "_errors": ["CANNOT_USE_SAME_PASSWORD"],
                    },
                    status=HTTP_400_BAD_REQUEST,
                )

        user = self.request.user
        if user.is_superuser is True:
            return self.set_password_and_return_resp(
                user=target_user, password=password
            )

        if user.is_at_least_staff is False or user <= target_user:
            return Response(
                data={'message': 'Does not have the permissions.'},
                status=HTTP_403_FORBIDDEN,
            )

        if user.admin is True:
            return self.set_password_and_return_resp(
                user=target_user, password=password
            )

        #:  If datamodel is scoped, a manager can change the password
        #:  of simpleusers only if they share a commun scope.
        #:  Otherwise if datamodel is not scoped, a manager cannot
        #:  change a simple user's password
        divider_attr_name = "{}s".format(DIVIDER_MODEL.lower())

        #:  Check divider abilities
        divider_target_related = getattr(target_user, divider_attr_name)
        divider_related = getattr(user, divider_attr_name)

        divider_target_uids = divider_target_related.values_list(
            'uid', flat=True
        )
        divider_uids = divider_related.values_list('uid', flat=True)

        if (divider_target_uids & divider_uids).exists() is False:
            return Response(
                data={'message': 'Does not have the permissions.'},
                status=HTTP_403_FORBIDDEN,
            )

        return self.set_password_and_return_resp(
            user=target_user, password=password
        )

    def post(self, request, *args, **kwargs):
        """
        :param request: needs fields
          **email**
          **password1**
          **password2**
        :return:
          return the UserSerializer data (email, url, first_name,
          last_name, password and token)
        """
        serializer = ChangePasswordSerializer(data=request.data)
        if not serializer.is_valid():
            #:  Do not give any info on this endpoint
            return Response(
                data={
                    "message": 'Invalid data format',
                    "_errors": ["INVALID_DATA"],
                },
                status=HTTP_400_BAD_REQUEST,
            )

        password1 = serializer.validated_data["password1"]
        password2 = serializer.validated_data["password2"]
        email = serializer.validated_data["email"].lower()
        password_change_token = serializer.validated_data.get(
            'password_change_token', None
        )

        #:  Check that target user exists
        target_user_qs = UserModel.objects.filter(email=email)
        if not target_user_qs.exists():
            return Response(
                data={'message': 'Invalid data', "_errors": ["INVALID_DATA"]},
                status=HTTP_400_BAD_REQUEST,
            )
        target_user = target_user_qs.first()

        #:  Check that the two passwords are identical
        if password1 != password2:
            return Response(
                data={
                    'message': 'Passwords not corresponding',
                    '_errors': ['MISMATCH_PASSWORDS'],
                },
                status=HTTP_400_BAD_REQUEST,
            )
        password = password1

        #:  Check that password is valid
        try:
            validator = ConcretePasswordValidator()
            validator(password)
        except PasswordInsecureValidationError as e:
            return Response(
                data={'message': e.message, "_errors": [e.code]},
                status=HTTP_400_BAD_REQUEST,
            )

        if password_change_token:
            return self.change_password_with_token(
                token=password_change_token,
                user=target_user,
                password=password,
            )
        #:  If user is anonymous, 400 with no info
        if request.user.is_anonymous:
            return Response(status=HTTP_400_BAD_REQUEST)
        user = request.user

        #:  a user is allowed to change his own password
        if email == user.email:
            if (
                user.password_has_expired
                or not settings.ALLOW_REUSE_PASSWORD_ON_CHANGE
            ):
                same_password = target_user.check_password(password)
                if same_password:
                    return Response(
                        data={
                            'message': 'New password must be different',
                            "_errors": ["CANNOT_USE_SAME_PASSWORD"],
                        },
                        status=HTTP_400_BAD_REQUEST,
                    )
            user.set_password(password)
            user.password_modification_date = date.today()
            user.save()
            resp_serializer = UserSerializer(
                instance=user, api_namespace=self.api_namespace
            )
            return Response(data=resp_serializer.data, status=HTTP_200_OK)

        return self.change_another_user_password(
            target_user=target_user, password=password
        )


class RegisterApiView(SecurityRulesMixin, generics.GenericAPIView):
    serializer_class = RegisterSerializer
    '''this view is used to register a new user. It first check
        if password1 == password2 and if email isn't already used
     '''
    api_namespace = DEFAULT_API_NAMESPACE

    def __init__(self, api_namespace, *args, **kwargs):
        self.api_namespace = api_namespace
        super().__init__(*args, **kwargs)

    def get_request_user(self):
        """
        :return: return the infos of the user who made the request
        """
        return self.request.user

    def get_entity_uid(self, request):
        return request.META.get("HTTP_X_ENTITY_UID", None)

    def get_divider(self):
        divider_uid = self.get_entity_uid(self.request)
        if divider_uid is None:
            return None
        try:
            return apps.get_model(
                "concrete.{}".format(DIVIDER_MODEL)
            ).objects.get(uid=divider_uid)
        except ObjectDoesNotExist:
            raise WrongEntityUIDError

    def can_access_user_obj(self, request_user, instance_user):
        # Super can access every instance
        if request_user.is_superuser:
            return True

        #: If the instance_user has a lower level, authorize
        if instance_user < request_user:
            return True
        #: If the instance_user has a greater level, deny
        if instance_user > request_user:
            return False

        #: if the level is the same, authorize
        return True

    def post(self, request, *args, **kwargs):
        """
        :param request: needs fields **email**,
           **password1** and **password2**
        :return: return the UserSerializer data
           (email, url, first_name, last_name, password and token)
        """
        divider_model_name = "{}s".format(DIVIDER_MODEL.lower())
        serializer = RegisterSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                data={
                    'message': 'serializer invalid',
                    "_errors": ["INVALID_DATA"],
                },
                status=HTTP_400_BAD_REQUEST,
            )

        request_user = self.get_request_user()
        at_least_staff = (
            False
            if request_user.is_anonymous
            else request_user.is_at_least_staff
        )
        try:
            divider = self.get_divider()
        except WrongEntityUIDError:
            divider = None
        # If no divider is given or the user is anonymous/simple user
        # Create the user without divider management
        if divider is None or not at_least_staff:
            return self.create_user(request, serializer, divider=None)
        has_not_divider = not self.has_divider(request_user, divider)

        # If the user is manager and has not the divider, refuse
        # An admin or super user can do it
        if has_not_divider and request_user.level == 'manager':
            return Response(
                data={
                    "message": (
                        "User is not allowed to add {} "
                        "he can't access".format(divider_model_name)
                    )
                },
                status=HTTP_403_FORBIDDEN,
            )
        return self.update_or_create_user_with_scope(
            request, serializer, divider
        )

    def create_user(self, request, serializer, divider=None):
        password1 = serializer.validated_data.get("password1", None)
        password2 = serializer.validated_data.get("password2", None)

        #:  If the two passwords are not set, a password is generated in case
        #:  of ALLOW_SEND_EMAIL_ON_REGISTER is True.
        #:  Otherwise, it's a bad request
        if password1 is None and password2 is None:
            if settings.ALLOW_SEND_EMAIL_ON_REGISTER is False:
                return Response(
                    data={
                        'message': 'serializer invalid',
                        "_errors": ["INVALID_DATA"],
                    },
                    status=HTTP_400_BAD_REQUEST,
                )
            send_register_email = True
            password = f"{uuid.uuid4()}-{uuid.uuid4()}-{uuid.uuid4()}"
            email_format = serializer.validated_data.get("email_format", None)
            request_user = self.get_request_user()
            user_not_allowed_to_email_format = (
                isinstance(request_user, AnonymousUser) is True
                or request_user.is_at_least_staff is False
            )
            if email_format is not None and user_not_allowed_to_email_format:
                return Response(
                    data={
                        'message': (
                            'Only registered users with a level of staff or '
                            'higher levels are allowed to set an email_format'
                        ),
                        '_errors': ['INVALID_PARAMETER'],
                    },
                    status=HTTP_400_BAD_REQUEST,
                )
            #:  Before creating the user, we check that url_format and
            #:  email_format have the right format
            url_format = serializer.validated_data["url_format"]
            if '{token}' not in url_format or '{email}' not in url_format:
                return Response(
                    data={
                        'errors': 'url_format is not a valid format_string',
                        '_errors': ['INVALID_PARAMETER'],
                    },
                    status=HTTP_400_BAD_REQUEST,
                )

            if email_format is not None and '{link}' not in email_format:
                return Response(
                    data={
                        'errors': 'email_format is not a valid format_string',
                        '_errors': ['INVALID_PARAMETER'],
                    },
                    status=HTTP_400_BAD_REQUEST,
                )

        else:
            send_register_email = False
            if not password1 == password2:
                return Response(
                    data={
                        'message': 'Password confimation incorrect',
                        '_errors': ['MISMATCH_PASSWORDS'],
                    },
                    status=HTTP_400_BAD_REQUEST,
                )
            password = password1
            try:
                validator = ConcretePasswordValidator()
                validator(password)
            except PasswordInsecureValidationError as e:
                return Response(
                    data={'message': e.message, "_errors": [e.code]},
                    status=HTTP_400_BAD_REQUEST,
                )

        #:  Force email to be lower
        email = serializer.validated_data["email"].lower()

        #:  Check Email matches REGEX settings
        if re.match(settings.API_REGISTER_EMAIL_FILTER, email) is None:
            return Response(
                data={
                    'message': 'This email is not allowed to register',
                    "_errors": ["EMAIL_NOT_AUTHORIZED_TO_REGISTER"],
                },
                status=HTTP_400_BAD_REQUEST,
            )

        #:  Add the fields in request.POST
        user_meta_model = meta_registered[settings.AUTH_USER_MODEL]
        user_model_field_names = [
            field[0] for field in user_meta_model.get_fields()
        ]
        data_to_post = {
            key: value
            for key, value in request.data.items()
            if key in user_model_field_names
        }
        data_to_post.update({'email': email})
        try:
            UserModel.objects.get(email=email)
            return Response(status=HTTP_200_OK)
        except UserModel.DoesNotExist:
            pass
        user = UserModel.objects.create(**data_to_post)

        user.set_password(password)
        user.save()
        if send_register_email is True:
            now = pendulum.now('utc')
            password_change_token_expiry_date = now.add(months=6)
            set_password_token = PasswordChangeToken.objects.create(
                user=user, expiry_date=password_change_token_expiry_date
            )
            url_format = serializer.validated_data["url_format"]

            #:  To avoid template injections, we use replace instead of format
            uri = url_format.replace(
                '{token}', str(set_password_token.uid)
            ).replace('{email}', user.email)

            referer = request.META.get(
                'HTTP_REFERER', settings.AUTH_CONFIRM_EMAIL_DEFAULT_REDIRECT_TO
            )

            email_format = (
                serializer.validated_data.get('email_format')
                or settings.DEFAULT_REGISTER_EMAIL_FORMAT
            )

            link = urljoin(referer, uri)

            email_body = email_format.replace('{link}', link)

            if settings.AUTH_CONFIRM_EMAIL_ENABLE is True:
                confirmation = user.get_or_create_confirmation(
                    redirect_to=link
                )

                if confirmation.link_sent is False:
                    confirmation.send_link(body=email_body)
            else:
                Email.objects.create(
                    subject=settings.REGISTER_EMAIL_SUBJECT,
                    resource_status='to-send',
                    resource_message='',
                    body=email_body,
                    receiver=user,
                    created_by=user,
                )

        elif settings.AUTH_CONFIRM_EMAIL_ENABLE is True:
            confirmation = user.get_or_create_confirmation(
                redirect_to=request.META.get('HTTP_REFERER')
            )

            if confirmation.link_sent is False:
                confirmation.send_link()

        serializer = UserSerializer(
            instance=user, api_namespace=self.api_namespace
        )
        if divider:
            return self.update_user_with_scope(
                request, serializer, divider, user, status=HTTP_201_CREATED
            )
        return Response(data=serializer.data, status=HTTP_201_CREATED)

    def update_or_create_user_with_scope(self, request, serializer, divider):
        email = serializer.validated_data["email"].lower()
        try:
            instance_user = UserModel.objects.get(email=email)
        # If the user does not exist, create it with the scope
        except ObjectDoesNotExist:
            return self.create_user(request, serializer, divider)
        else:
            # if the user exists, update it if authorized
            request_user = self.get_request_user()
            if not self.can_access_user_obj(request_user, instance_user):
                return Response(
                    data={
                        "message": (
                            "{} is not allowed to update a user with "
                            "level {}".format(
                                request_user.level, instance_user.level
                            )
                        )
                    },
                    status=HTTP_403_FORBIDDEN,
                )
            return self.update_user_with_scope(
                request, serializer, divider, instance_user, status=HTTP_200_OK
            )

    def update_user_with_scope(
        self, request, serializer, divider, instance_user, status=HTTP_200_OK
    ):
        # Get user dividers field and add the request divider
        divider_model_name = "{}s".format(DIVIDER_MODEL.lower())
        user_dividers = getattr(instance_user, divider_model_name)
        user_dividers.add(divider)

        serializer = UserSerializer(
            instance=instance_user, api_namespace=self.api_namespace
        )

        return Response(data=serializer.data, status=status)

    def has_divider(self, user, divider):
        # If the user has the divider, return True
        divider_model_name = "{}s".format(DIVIDER_MODEL.lower())
        user_dividers_manager = getattr(user, divider_model_name)
        return divider in user_dividers_manager.all()


class ResetPasswordApiView(SecurityRulesMixin, generics.GenericAPIView):
    serializer_class = ResetPasswordSerializer

    def post(self, request, *args, **kwargs):
        serializer = ResetPasswordSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                data={
                    'message': serializer.errors,
                    "_errors": ["INVALID_DATA"],
                },
                status=HTTP_400_BAD_REQUEST,
            )

        email = serializer.validated_data["email"].lower()

        user_queryset = UserModel.objects.filter(email=email, is_active=True)
        if not user_queryset.exists():
            return Response(
                data={'message': 'invalid data', "_errors": ["INVALID_DATA"]},
                status=HTTP_400_BAD_REQUEST,
            )

        user = user_queryset.first()

        reset_token = PasswordChangeToken.objects.create(user=user)

        url_format = serializer.validated_data["url_format"]
        if '{token}' not in url_format or '{email}' not in url_format:
            return Response(
                data={
                    'message': 'url_format is not a valid format_string',
                    '_errors': ['INVALID_PARAMETER'],
                },
                status=HTTP_400_BAD_REQUEST,
            )
        uri = url_format.replace('{token}', str(reset_token.uid)).replace(
            '{email}', user.email
        )

        referer = request.META.get(
            'HTTP_REFERER', settings.AUTH_CONFIRM_EMAIL_DEFAULT_REDIRECT_TO
        )

        link = urljoin(referer, uri)

        self.send_email(link=link, user=user, created_by=user)

        return Response(data={'email': user.email}, status=HTTP_200_OK)

    def send_email(self, link, user, created_by):

        Email.objects.create(
            subject="Reset password",
            resource_status='to-send',
            resource_message='',
            body=settings.AUTH_CONFIRM_RESET_PASSWORD_EMAIL_BODY.format(
                link=link
            ),
            receiver=user,
            created_by=created_by,
        )


class AccountMeApiView(
    generics.RetrieveAPIView, generics.UpdateAPIView, generics.GenericAPIView
):

    model_class = UserModel
    authentication_classes = (
        authentication.SessionAuthentication,
        TokenExpiryAuthentication,
        URLTokenExpiryAuthentication,
    )
    permission_classes = (UserAccessPermission,)
    api_namespace = DEFAULT_API_NAMESPACE

    def __init__(self, api_namespace, *args, **kwargs):
        self.api_namespace = api_namespace
        super().__init__(*args, **kwargs)

    def get_serializer_class(self):
        return make_account_me_serialier(self.api_namespace)

    def get_object(self):
        """
        :return: return the infos of the user who made the request
        """
        return self.request.user

    def update(self, request, *args, **kwargs):
        # Validator on update does not validate password
        # It should be performed within this view on perform_update
        try:
            return super(AccountMeApiView, self).update(
                request, *args, **kwargs
            )
        except PasswordInsecureValidationError as e:
            return Response(
                data={'message': e.message, "_errors": [e.code]},
                status=HTTP_400_BAD_REQUEST,
            )

    def perform_update(self, serializer):
        """
        update user's infos on the requested
            fields(**email**, **password**, **first_name**...)
        """
        # Validator on update does not validate password
        # It should be performed within this view
        # It will raise a PasswordInsecureValidationError if password
        # is not valid
        pwd = serializer.validated_data.get('password')
        if pwd:
            pwd_validator = ConcretePasswordValidator()
            pwd_validator(pwd)
        email = serializer.validated_data.get('email')
        if email:
            instance = serializer.save(email=email.lower())
        else:
            instance = serializer.save()
        if pwd:
            instance.set_password(pwd)
            instance.save()


class PaginatedViewSet(object):
    pagination_class = ExtendedPagination
    filter_backends = (
        FilterDistanceBackend,
        SearchFilter,
        OrderingFilter,
        FilterSupportingOrBackend,
        FilterSupportingEmptyBackend,
        FilterSupportingContainsBackend,
        FilterSupportingRangeBackend,
        FilterUserByLevel,
        FilterSupportingComparaisonBackend,
        DjangoFilterBackend,
        FilterSupportingComparaisonBackend,
        FilterForeignKeyIsNullBackend,
        FilterSupportingForeignKey,
        FilterSupportingManyToMany,
    )
    filterset_fields = ()
    ordering_fields = '__all__'
    ordering = ('-creation_date',)
    basename = None

    def get_list_display(self):
        return []  # skip-test-coverage

    def get_flat_serializer(self, *args, **kwargs):
        return self.get_serializer(*args, **kwargs)

    @action(detail=False, url_path='export', url_name='export')
    def get_export(self, request):
        if request.parser_context["view"].model_class.__name__ == "User":
            validate_request_permissions(request=request)

        if not self.export_fields:
            return Response(status=HTTP_204_NO_CONTENT)
        export_fields = self.export_fields

        queryset = self.filter_queryset(self.get_queryset())
        export_queryset = queryset.values(*export_fields)

        response = csv_streaming_response(
            request, export_queryset, export_fields
        )

        return response

    @action(
        detail=False,
        url_path='stats{}'.format(URL_TIMESTAMP),
        url_name='stats',
    )
    def get_stats(self, request, timestamp_start=None, timestamp_end=None):
        if request.parser_context["view"].model_class.__name__ == "User":
            validate_request_permissions(request=request)

        # Get urls for the subpages from the stats url
        parsed_url = urlparse(self.request.build_absolute_uri())
        # Delete /stats/ from url
        parsed_url = parsed_url._replace(
            path=parsed_url.path.split('stats/')[0]
        )
        url_query = parsed_url.query
        # Reformat timestamps, add them to query params of request
        if timestamp_start:
            if url_query == '':
                url_query = f'timestamp_start={timestamp_start}'
            else:
                url_query += f'&timestamp_start={timestamp_start}'
        if timestamp_end:
            if url_query == '':
                url_query = f'timestamp_end={timestamp_end}'
            else:
                url_query += f'&timestamp_end={timestamp_end}'

        url = urlunparse(parsed_url._replace(query=url_query))

        queryset, timestamp_end = self._get_queryset_filtered_since_timestamp(
            timestamp_start, timestamp_end
        )

        _resp = self.get_paginated_response(
            self.request.data,
            timestamp_start=timestamp_start,
            timestamp_end=timestamp_end,
        )

        _total = queryset.count()

        _num_pages = _resp.data['num_total_pages']

        dict_pages = dict()

        for page_number in range(1, _num_pages + 1):
            if page_number == 1:
                dict_pages['page{}'.format(page_number)] = unquote(
                    remove_query_param(url, 'page')
                )
            else:
                dict_pages['page{}'.format(page_number)] = unquote(
                    replace_query_param(url, 'page', page_number)
                )

        data = {
            'objects_count': _total,
            'timestamp_start': timestamp_start or 0.0,
            'timestamp_end': timestamp_end,
            'num_total_pages': _num_pages,
            'max_allowed_objects_per_page': _resp.data[
                'max_allowed_objects_per_page'
            ],
            'page_urls': dict_pages,
        }
        return Response(data)

    def _get_queryset_filtered_since_timestamp(
        self, timestamp_start=None, timestamp_end=None
    ):
        queryset = self.filter_queryset(self.get_queryset())

        if timestamp_start is not None:
            timestamp_start = timestamp_start
            queryset, timestamp_end = apply_filter_since(
                queryset, timestamp_start, timestamp_end
            )
        else:
            timestamp_end = 0.0

        return queryset, timestamp_end

    def get_extra_informations(self, queryset):
        _model_class = self.model_class or queryset.model
        extra_info = {
            'model_name': _model_class.__name__,
            'model_verbose_name': _model_class._meta.verbose_name,
            'list_display': self.get_list_display(),
            'list_filter': self.get_list_filters_field(queryset),
            'total_objects_count': queryset.count(),
            'create_url': self.request.build_absolute_uri(
                reverse(
                    "{}:{}-list".format(DEFAULT_API_NAMESPACE, self.basename)
                )
            ),
        }
        if _model_class.__name__ == 'User':
            extra_info['create_url'] = self.request.build_absolute_uri(
                reverse("{}:register-view".format(DEFAULT_API_NAMESPACE))
            )
        return extra_info

    def get_list_filters_field(self, queryset):
        return {
            field_name: set(queryset.values_list(field_name, flat=True))
            for field_name in self.filterset_fields
        }

    def get_paginated_response(
        self, data, timestamp_start=None, timestamp_end=None
    ):
        if timestamp_start is None:
            timestamp_start = self.request.GET.get('timestamp_start')
        incremental_loading = timestamp_start is not None
        timestamp_start = parse_to_float(timestamp_start)
        if timestamp_end is None:
            timestamp_end = self.request.GET.get('timestamp_end')
        timestamp_end = parse_to_float(timestamp_end)
        if timestamp_end == 0.0:
            timestamp_end = None

        all_instances = self.get_queryset()
        queryset = self.filter_queryset(all_instances)
        excluded_instances = all_instances.exclude(
            pk__in=list(queryset.values_list('pk', flat=True))
        )

        extra_informations = self.get_extra_informations(queryset=queryset)

        if incremental_loading:
            deleted_uids = []

            queryset, timestamp_end = apply_filter_since(
                queryset, timestamp_start, timestamp_end
            )

            if timestamp_start < 0:
                error_message = (
                    'wrong argument: timestamp_start has to be a float '
                    'greater than 0.0'
                )
                return Response(
                    data={
                        'message': error_message,
                        '_errors': ['INVALID_QUERY'],
                    },
                    status=HTTP_400_BAD_REQUEST,
                )

            if timestamp_start > 0.0:
                #: Retrieve deleted model instances
                deleted_instances = DeletedModel.objects.filter(
                    model_name=queryset.model.__name__
                )

                #: Exclude deleted instances before `timestamp_start`
                deleted_instances_since, _ = apply_filter_since(
                    deleted_instances, timestamp_start, timestamp_end
                )

                #: Retrieve instances that used to match our filters before
                #: `timestamp_start` but that were modified since
                excl_modified_instances, _ = apply_filter_since(
                    excluded_instances, timestamp_start, timestamp_end
                )

                #: Format as list
                deleted_uids = set(
                    chain(
                        deleted_instances_since.values_list('uid', flat=True),
                        excl_modified_instances.values_list('uid', flat=True),
                    )
                )
                deleted_uids = list(deleted_uids)

            extra_informations.update(
                {
                    'timestamp_start': timestamp_start or 0.0,
                    'timestamp_end': timestamp_end,
                    'deleted_uids': deleted_uids,
                }
            )

        c_resp_page_size = self.request.GET.get(
            'c_resp_page_size',
            settings.REST_FRAMEWORK.get(
                'PAGE_SIZE', settings.API_MAX_PAGINATION_SIZE
            ),
        )

        try:
            c_resp_page_size = int(c_resp_page_size)
            if c_resp_page_size < 1:
                raise ValueError

        except ValueError:
            error_message = (
                'wrong argument: c_resp_page_size has to be a number between'
                ' 1 and {}'.format(settings.API_MAX_PAGINATION_SIZE)
            )
            return Response(
                data={'message': error_message, '_errors': ['INVALID_QUERY']},
                status=HTTP_400_BAD_REQUEST,
            )

        #: Paginate the new queryset
        page_as_list = self.paginate_queryset(queryset)

        c_resp_nested = self.request.GET.get('c_resp_nested', 'true')
        if c_resp_nested not in ['true', 'false']:
            return Response(
                data={
                    'message': (
                        "wrong argument: c_resp_nested has to be wether "
                        "'true' or 'false'"
                    ),
                    '_errors': ['INVALID_QUERY'],
                },
                status=HTTP_400_BAD_REQUEST,
            )
        if c_resp_nested == 'false':
            serializer = self.get_flat_serializer(page_as_list, many=True)
            data = serializer.data
        else:
            serializer = self.get_serializer(page_as_list, many=True)
            data = serializer.data
        resp = super(PaginatedViewSet, self).get_paginated_response(data)

        # Add timestamp_end within urls
        if timestamp_start is not None:
            next_link = resp.data.get('next')
            if next_link is not None:
                next_link = replace_query_param(
                    next_link, 'timestamp_end', timestamp_end
                )
                resp.data.update(next=next_link)

            previous_link = resp.data.get('previous')
            if previous_link is not None:
                previous_link = replace_query_param(
                    previous_link, 'timestamp_end', timestamp_end
                )
                resp.data.update(previous=previous_link)

        resp.data.update(extra_informations)
        resp.data.update({'objects_count': len(resp.data.get('results', []))})
        return resp


class ApiModelViewSet(PaginatedViewSet, viewsets.ModelViewSet):
    authentication_classes = (
        authentication.BasicAuthentication,
        authentication.SessionAuthentication,
        TokenExpiryAuthentication,
        URLTokenExpiryAuthentication,
    )

    def dispatch(self, request, *args, **kwargs):
        # Retrieve response first then log
        rsp = super(ApiModelViewSet, self).dispatch(request, *args, **kwargs)
        # Extract request infos
        ip = get_client_ip(request)
        verbose_method = {
            "GET": "READ",
            "PUT": "UPDATE",
            "PATCH": "UPDATE",
            "POST": "CREATE",
        }
        # NB: use of self.request instead of request, because the super of
        # dispatch() update request object while calling initialize_request()
        now = pendulum.now('utc').format(settings.LOGGING['datefmt'])
        user = self.request.user
        method = self.request.method
        model_name = self.serializer_class.Meta.model.__name__
        data = self.request.data
        pk = self.kwargs.get('pk')

        if method in ["GET", "OPTIONS", "HEAD"]:
            api_logger = logger_api_safe
        else:
            api_logger = logger_api_unsafe
            token_in_header = self.request.META.get(
                "HTTP_AUTHORIZATION", ""
            ).split('Token ')[-1]
            auth_token = AuthToken.objects.filter(key=token_in_header)
            # Update the token last action for expiry (QuerySet of 1 token)
            if auth_token:
                auth_token.update(last_action_date=pendulum.now('utc'))

        # Base log message
        base_message = (
            f"[{now}|{ip}|{user}|{verbose_method.get(method, method)}] "
        )

        # Format message depending on request method
        if method == "GET":
            if pk:
                verbose_message = f"Access instance {pk} of model {model_name}"
            else:
                verbose_message = f"List instances of model {model_name}"
                if self.kwargs:
                    verbose_message += f" with params {self.kwargs}"
        elif method == "POST":
            verbose_message = f"Create new instance of model {model_name} with data {dict(data)}"
        elif method in ["PUT", "PATCH"]:
            if not pk:
                verbose_message = "UID missing in request url"
            else:
                verbose_message = (
                    f"Update instance {pk} of model {model_name} "
                    f"with data {dict(data)}"
                )
        elif method == "DELETE":
            verbose_message = f"Delete instance {pk} of model {model_name}"
        else:
            verbose_message = ""
        # Log the request
        log_request = base_message + "Request To " + verbose_message
        api_logger.info(log_request)

        # Log the response status code
        log_response = base_message + "Response: " + f" {rsp.status_code}"
        api_logger.info(log_response)

        # Return the dispatch response
        return rsp

    def list(self, request):
        def check_date_format(date_type, param_values):
            if date_type == "DateField":
                regex = r'^\d{4}-\d{2}-\d{2}$'
                date_format = 'yyyy-mm-dd'
            else:
                regex = r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$'
                date_format = 'yyyy-mm-ddThh:mm:ssZ'

            wrong_format = any(
                map(
                    lambda x: re.match(regex, x) is None,
                    filter(lambda x: x != '', param_values),
                )
            )
            if wrong_format:
                return (
                    False,
                    Response(
                        data={
                            'message': "Wrong date format, should be '{}'".format(
                                date_format
                            ),
                            '_errors': ['INVALID_QUERY'],
                        },
                        status=HTTP_400_BAD_REQUEST,
                    ),
                )
            else:
                return True, None

        for query_param in request.GET:
            param_values_list = request.GET[query_param].split(',')
            param = query_param.split('__')[0].replace('_uid', '')
            if param not in self.fields:
                continue
            if param not in self.filterset_fields:
                return Response(
                    data={
                        'message': 'filter against {} is not allowed'.format(
                            param
                        ),
                        '_errors': ['INVALID_QUERY'],
                    },
                    status=HTTP_400_BAD_REQUEST,
                )
            param_type = (
                self.get_queryset()
                .model._meta.get_field(param)
                .get_internal_type()
            )
            if param_type in ('DateField', 'DateTimeField'):
                right_format, resp = check_date_format(
                    date_type=param_type, param_values=param_values_list
                )
                if right_format is False:
                    return resp

        #: we overrided get_paginated_response and we re-create data.
        #: So we set it to None until refactoring the code.
        return self.get_paginated_response(data=None)

    def get_entity_uid(self, request):
        scope_header_uid = request.META.get("HTTP_X_ENTITY_UID", None)
        try:
            uid = uuid.UUID(str(scope_header_uid), version=4)
            if uid.hex == str(scope_header_uid).replace('-', ''):
                return scope_header_uid
        except ValueError:
            if scope_header_uid is not None:
                # Scope is not a valide UID, raise SuspiciousOperation to return 400
                raise SuspiciousOperation("X_ENTITY_UID is not a valid UUID")
        return None

    def get_divider(self):
        model_name = self.__class__.model_class.__name__
        model_is_divider = model_name == DIVIDER_MODEL
        if model_is_divider:
            return None

        model_not_divided = model_name in UNDIVIDED_MODEL
        model_not_user = model_name.lower() != 'user'
        # If it is not divider and it is not the model user, return none
        # Continue if the model is divided or it is the model user
        if model_not_divided and model_not_user:
            return None

        divider_uid = self.get_entity_uid(self.request)
        if divider_uid is None:
            return None

        try:
            return apps.get_model(
                "concrete.{}".format(DIVIDER_MODEL)
            ).objects.get(uid=divider_uid)
        except ObjectDoesNotExist:
            raise WrongEntityUIDError

    def get_queryset(self):
        #: If divided model
        user = self.request.user
        # superuser = user.is_superuser is True
        at_least_admin = False if user.is_anonymous else user.is_at_least_admin
        at_least_staff = False if user.is_anonymous else user.is_at_least_staff

        try:
            divider = self.get_divider()
        except WrongEntityUIDError:
            return self.model_class.objects.none()

        model_name = self.model_class.__name__

        if model_name == DIVIDER_MODEL and divider is None:
            if user.is_anonymous:
                return self.model_class.objects.filter(public=True)
            elif at_least_admin:
                return self.model_class.objects.all()
            else:
                return self.model_class.objects.filter(
                    pk__in=getattr(
                        user, '{}s'.format(DIVIDER_MODEL.lower())
                    ).all()
                )

        if self.model_class is UserModel:

            #: Anonymous user can only see public objects
            divider_name_plural = '{}s'.format(DIVIDER_MODEL.lower())
            user_filters = {'is_active': True}
            if divider:
                user_filters.update({divider_name_plural: divider.pk})

            if at_least_staff:
                return UserModel.objects.filter(**user_filters)
            user_filters.update(public=True)
            return UserModel.objects.filter(**user_filters)

        queryset = filter_queryset_by_permissions(
            queryset=self.model_class.objects.all(),
            user=self.request.user,
            divider=divider,
        )

        if divider is not None:
            queryset = filter_queryset_by_divider(
                queryset=queryset, user=self.request.user, divider=divider
            )

        if self.request.method in permissions.SAFE_METHODS:
            rel_fields = self.rel_single_fields + self.rel_iterable_fields
            rel_fields += [
                'can_view_users',
                'can_view_groups',
                'can_admin_users',
                'can_admin_groups',
            ]
            return queryset.prefetch_related(*rel_fields)
        else:
            return queryset

    def get_list_display(self):
        if self.list_display is None:
            raise ValueError(
                f"'{self.__class__.__name__}' should either include a "
                "`list_display` attribute, or override the "
                "`get_list_display()` method."
            )
        return self.list_display

    def get_serializer(self, *args, **kwargs):
        """
        Return the serializer instance that should be used for validating and
        deserializing input, and for serializing output.
        """
        serializer_class = self.get_serializer_class()

        kwargs['context'] = self.get_serializer_context()
        return serializer_class(*args, **kwargs)

    def get_serializer_class(self):
        if self.request.method in permissions.SAFE_METHODS:
            return self.get_nested_serializer_class()

        return self.get_flat_serializer_class()

    def get_flat_serializer(self, *args, **kwargs):
        serializer_class = self.get_flat_serializer_class()

        kwargs['context'] = self.get_serializer_context()
        return serializer_class(*args, **kwargs)  # pylint:disable=E1102

    def get_flat_serializer_class(self):
        return self.serializer_class

    def get_nested_serializer_class(self):
        return self.serializer_class_nested

    def perform_create(self, serializer):

        attrs = {'created_by': self.request.user}

        try:
            divider = self.get_divider()
        except WrongEntityUIDError:
            divider = None

        if divider is not None:
            attrs.update({DIVIDER_MODEL.lower(): divider})

        for name in self.file_fields:
            file_data = self.request.data.get(name, None)
            if file_data is not None:
                attrs.update({name: self.request.data.get(name)})

        serializer.save(**attrs)

    def create(self, *args, **kwargs):
        return super(ApiModelViewSet, self).create(*args, **kwargs)

    def handle_divider_update(self, request, request_user, instance):
        divider_model_name = "{}s".format(DIVIDER_MODEL.lower())
        # The request is either a simple dict or a QueryDict
        data = dict(request.data)
        new_dividers = data.get(divider_model_name, None)
        # If no divider is given, do nothing
        if new_dividers is not None:
            #: The request user can't change his own scope
            if request_user.pk == instance.pk:
                return Response(
                    data={
                        "message": (
                            "User can't change his field {}".format(
                                divider_model_name
                            )
                        )
                    },
                    status=HTTP_403_FORBIDDEN,
                )
            instance_dividers = getattr(instance, divider_model_name, None)
            request_user_dividers = getattr(
                request_user, divider_model_name, None
            )
            if instance_dividers:
                instance_dividers_all = {
                    str(p.uid) for p in instance_dividers.all()
                }
            else:
                instance_dividers_all = set()

            if request_user_dividers is not None:
                request_user_dividers_all = {
                    str(p.uid) for p in request_user_dividers.all()
                }
            else:
                request_user_dividers_all = set()
            #: Keep only new divider, not divider already in the instance
            set_new_dividers = set(new_dividers) - instance_dividers_all
            # If the new dividers are not the same as the request user, forbid the action
            if set_new_dividers.difference(request_user_dividers_all):
                return Response(
                    data={
                        "message": (
                            "User is not allowed to add {} "
                            "he can't access".format(divider_model_name)
                        )
                    },
                    status=HTTP_403_FORBIDDEN,
                )

            # Union of previous and new dividers to prevent divider removal if same level
            if request_user.level == instance.level:
                union_dividers = set_new_dividers.union(instance_dividers_all)
            else:
                union_dividers = new_dividers
            data[divider_model_name] = list(union_dividers)
            if isinstance(request.data, QueryDict):
                request.POST._mutable = True
                request.data.setlist(divider_model_name, list(union_dividers))
                request.POST._mutable = False
            else:
                request.data[divider_model_name] = list(union_dividers)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        if isinstance(instance, UserModel):
            request_user = request.user
            at_least_admin = request_user.is_at_least_admin
            if not at_least_admin:
                res = self.handle_divider_update(
                    request, request_user, instance
                )
                if res:
                    return res
        return super(ApiModelViewSet, self).update(request, *args, **kwargs)

    def perform_update(self, serializer):
        attrs = {}
        instance = self.get_object()
        divider_model_name = "{}s".format(DIVIDER_MODEL.lower())
        data = dict(self.request.data)
        # If it is an User and the divider is in the data
        if isinstance(instance, UserModel) and divider_model_name in data:
            # Get the divider that are removed to update
            # instances linked to the user with the divider

            old_divider_qs = getattr(instance, divider_model_name, None)

            if old_divider_qs:
                old_divider_set = {str(p.uid) for p in old_divider_qs.all()}
            else:
                old_divider_set = set()
            new_dividers_list = data.get(divider_model_name)
            new_dividers_set = set(new_dividers_list)
            removed_dividers_pks = old_divider_set.difference(new_dividers_set)
            # If divider are removed, handle the divider removal
            if removed_dividers_pks:
                remove_instances_user_tracked_fields(
                    instance, removed_dividers_pks
                )

        for name in self.file_fields:
            file_data = self.request.data.get(name, None)
            if file_data is not None:
                attrs.update({name: self.request.data.get(name)})

        serializer.save(**attrs)

    def block_user(self, instance_user):
        instance_user.set_level("blocked")
        instance_user.save()
        return Response(status=HTTP_204_NO_CONTENT)

    def remove_user_divider(self, instance_user, divider):
        divider_model_name = "{}s".format(DIVIDER_MODEL.lower())
        instance_divider_manager = getattr(instance_user, divider_model_name)
        instance_divider_manager.remove(divider)
        return Response(status=HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if not isinstance(instance, UserModel):
            try:
                return super(ApiModelViewSet, self).destroy(
                    request, *args, **kwargs
                )
            except ProtectedError as e:
                protected_objects_qs = e.protected_objects
                related_model = protected_objects_qs.model
                msg = (
                    'Attempting to delete a protected related instance: '
                    f'related to instance(s) {[str(o.uid) for o in protected_objects_qs]}'
                    f' of model {related_model.__name__}'
                )
                return Response(
                    status=HTTP_412_PRECONDITION_FAILED,
                    data={'message': msg, '_errors': ["PROTECTED_RELATION"]},
                )
        divider = self.get_divider()
        if divider is None:
            return self.block_user(instance)
        else:
            remove_instances_user_tracked_fields(instance, [divider])
            return self.remove_user_divider(instance, divider)


def unauthorized(*args, **kwargs):
    return Response(status=HTTP_403_FORBIDDEN)


def make_api_viewset_generic_attributes_class(
    meta_model,
    api_namespace,
    make_serializer_class_fct,
    model_permission_classes,
):
    from concrete_datastore.concrete.models import UNDIVIDED_MODEL

    is_divided = meta_model.get_model_name() not in UNDIVIDED_MODEL
    not_divider = meta_model.get_model_name() != DIVIDER_MODEL
    model_filterset_fields = tuple(
        meta_model.get_property('m_filter_fields', [])
    )
    not_user = meta_model.get_model_name().lower() != 'user'
    if is_divided and not_divider and not_user:
        model_filterset_fields += ('{}'.format(DIVIDER_MODEL.lower()),)

    class GenericAttributesViewsetClass:

        permission_classes = model_permission_classes

        model_class = main_app.models[meta_model.get_model_name().lower()]
        list_display = meta_model.get_property('m_list_display') or []
        ordering_fields = tuple(meta_model.get_property('m_list_display', []))
        search_fields = tuple(meta_model.get_property('m_search_fields', []))
        filterset_fields = model_filterset_fields
        distance_filter_field = meta_model.get_property(
            'm_distance_filter_field'
        )
        export_fields = tuple(meta_model.get_property('m_export_fields', []))
        fields = [f for f, _ in meta_model.get_fields()]
        serializer_class = make_serializer_class_fct(
            meta_model=meta_model, nested=False, api_namespace=api_namespace
        )
        serializer_class_nested = make_serializer_class_fct(
            meta_model=meta_model, nested=True, api_namespace=api_namespace
        )
        basename = meta_model.get_dashed_case_class_name()
        file_fields = [
            name
            for name, field in meta_model.get_fields()
            if field.f_type == 'FileField'
        ]
        rel_single_fields = [
            f
            for f, fspec in meta_model.get_fields()
            if fspec.type == 'rel_single'
        ]
        rel_iterable_fields = [
            f
            for f, fspec in meta_model.get_fields()
            if fspec.type == 'rel_iterable'
        ]

    return GenericAttributesViewsetClass


def make_api_viewset(
    meta_model,
    api_namespace=DEFAULT_API_NAMESPACE,
    permission_classes=(UserAccessPermission,),
    api_model_view_set_class=None,
    make_serializer_class_fct=None,
):
    if make_serializer_class_fct is None:
        make_serializer_class_fct = make_serializer_class

    attrs = {}

    if meta_model.get_model_name() == 'User':
        attrs.update({'create': unauthorized})

    if api_model_view_set_class is None:
        api_model_view_set_class = ApiModelViewSet

    api_model_view_set = type(
        str('{}ModelViewSet'.format(meta_model.get_model_name())),
        (
            make_api_viewset_generic_attributes_class(
                meta_model=meta_model,
                api_namespace=api_namespace,
                make_serializer_class_fct=make_serializer_class_fct,
                model_permission_classes=permission_classes,
            ),
            api_model_view_set_class,
        ),
        attrs,
    )

    return api_model_view_set


CONCRETE_SETTINGS = getattr(settings, 'CONCRETE', {})
API_PERMISSIONS_CLASSES = CONCRETE_SETTINGS.get('API_PERMISSIONS_CLASSES', {})

for meta_model in list_of_meta:
    if meta_model.get_model_name() in ["EntityDividerModel", "UndividedModel"]:
        continue

    permissions_classes_path = API_PERMISSIONS_CLASSES.get(
        meta_model._specifier.name,
        ('concrete_datastore.api.v1.permissions.UserAccessPermission',),
    )

    permissions_classes = ()

    for permission_class_path in permissions_classes_path:
        module = import_module(
            permission_class_path[: permission_class_path.rfind('.')]
        )

        try:
            permissions_classes += (
                getattr(module, permission_class_path.split('.')[-1]),
            )
        except AttributeError:
            raise RuntimeError(
                'CONCRETE impoperly configured : unknown '
                'permission class {}'.format(permission_class_path)
            )

    viewset_name = '{}ModelViewSet'.format(meta_model.get_model_name())

    setattr(
        sys.modules[__name__],
        viewset_name,
        make_api_viewset(
            meta_model=meta_model,
            permission_classes=permissions_classes,
            api_namespace=DEFAULT_API_NAMESPACE,
        ),
    )
