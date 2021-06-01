# coding: utf-8
import sys
import uuid
import logging
import pendulum
import warnings

from django.conf import settings
from django.utils import timezone
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model, authenticate
from django.core.exceptions import ObjectDoesNotExist
from django.http.response import HttpResponseNotAllowed

from rest_framework import mixins, authentication, generics, viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.reverse import reverse
from rest_framework.status import (
    HTTP_403_FORBIDDEN,
    HTTP_400_BAD_REQUEST,
    HTTP_401_UNAUTHORIZED,
    HTTP_200_OK,
    HTTP_202_ACCEPTED,
    HTTP_201_CREATED,
    HTTP_409_CONFLICT,
)

from concrete_datastore.api.v1_1.permissions import (
    ConcreteRolesPermission,
    BlockedUsersPermission,
)
from concrete_datastore.concrete.meta import list_of_meta
from concrete_datastore.api.v1.serializers import (
    UserSerializer,
    make_serializer_class,
)
from concrete_datastore.api.v1_1.serializers import (
    make_account_me_serialier,
    ConcreteRoleSerializer,
    ConcretePermissionSerializer,
    ProcessRegisterSerializer,
    LDAPAuthLoginSerializer,
    EmailDeviceSerializer,
    TwoFactorLoginSerializer,
    BlockedUserUpdateSerializer,
)
from concrete_datastore.api.v1.authentication import (
    TokenExpiryAuthentication,
    expire_temporary_tokens,
    URLTokenExpiryAuthentication,
)
from concrete_datastore.api.v1.views import (
    validate_request_permissions,
    make_api_viewset,
    unauthorized,
    URL_TIMESTAMP,
    AccountMeApiView as ApiV1AccountMeApiView,
    ApiModelViewSet as ApiV1ModelViewSet,
    PaginatedViewSet,
)
from concrete_datastore.api.v1.permissions import (
    get_permissions_classes_by_meta_model,
)
from concrete_datastore.api.v1 import DEFAULT_API_NAMESPACE
from concrete_datastore.api.v1_1 import API_NAMESPACE

from concrete_datastore.concrete.models import (
    get_fields_and_types_of_model,
    ConcreteRole,
    ConcretePermission,
    EmailDevice,
    AuthToken,
)
from concrete_datastore.concrete.automation.signals import user_logged_in


UserModel = get_user_model()

logger = logging.getLogger('concrete-datastore')
logger_api_auth = logging.getLogger('api_auth_log')


def get_client_ip(request):
    if 'HTTP_X_FORWARDED_FOR' in request.META:
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


class LDAPLoginApiView(generics.GenericAPIView):
    """this view is used to login the user"""

    #: Serializer
    serializer_class = LDAPAuthLoginSerializer
    api_namespace = API_NAMESPACE

    def post(self, request, *args, **kwargs):
        """
        :param request: needs fields **email** & **password**
        :return:
          return the UserSerializer data (email, url, first_name,
          last_name, level, password and token)
        """
        serializer = LDAPAuthLoginSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                data=serializer.errors, status=HTTP_400_BAD_REQUEST
            )

        username = serializer.validated_data["username"]

        user = authenticate(
            username=username,
            password=serializer.validated_data["password"],
            from_api=True,
        )
        if user is None:
            return Response(
                data={
                    'message': 'Wrong auth credentials',
                    "_errors": ["WRONG_AUTH_CREDENTIALS"],
                },
                status=HTTP_401_UNAUTHORIZED,
            )

        user_logged_in.send(sender=get_user_model(), user=user)

        get_user_model().objects.filter(pk=user.pk).update(
            last_login=timezone.now()
        )

        serializer = UserSerializer(
            instance=user, api_namespace=self.api_namespace
        )
        return Response(data=serializer.data, status=HTTP_200_OK)


class ProcessRegisterApiView(generics.GenericAPIView):
    serializer_class = ProcessRegisterSerializer

    def post(self, request, *args, **kwargs):

        """
        1. Check if the token is not already created and that it is valid
        2. Check if the user(process) is not already created with a different token
        """
        serializer = self.serializer_class(data=request.data)
        if not serializer.is_valid():
            return Response(
                data={'message': serializer.errors},
                status=HTTP_400_BAD_REQUEST,
            )
        application = serializer.validated_data["application"]
        instance = serializer.validated_data["instance"]
        email = "{}_{}@netsach.com".format(application, instance).lower()
        logger.info(f'Process {application} {instance} is trying to register')
        token = serializer.validated_data["token"]
        auth_token = AuthToken.objects.filter(key=token, expired=False).first()
        if auth_token:
            # If the emails match, it is authorized
            if auth_token.user.email == email:
                data = {
                    "msg": "Process successfully registered",
                    "token": token,
                    "level": auth_token.user.get_level(),
                }
                return Response(data=data, status=HTTP_202_ACCEPTED)
            # If they do not match, conflict
            else:
                data = {
                    "msg": "Email address already used with a different token"
                }
                return Response(data=data, status=HTTP_409_CONFLICT)

        password = str(uuid.uuid4())
        user, created = UserModel.objects.get_or_create(email=email)
        if created:
            user.set_password(password)
            user.set_level('blocked')
            user.save()
        else:
            # If the email address already has a token, unauthorize
            existing_token = user.auth_tokens.exclude(key=token).first()
            if existing_token is not None:
                data = {
                    "msg": "Email address already used with a different token"
                }
                return Response(data=data, status=HTTP_409_CONFLICT)
        now = pendulum.now('utc')
        now_plus_100_years = now.add(years=100)
        AuthToken.objects.create(
            key=token, user=user, expiration_date=now_plus_100_years
        )

        data = {
            "msg": "Process successfully registered",
            "token": token,
            "level": user.get_level(),
        }

        return Response(status=HTTP_202_ACCEPTED, data=data)


class ApiModelViewSet(ApiV1ModelViewSet):
    @action(
        detail=False, url_path='sets{}'.format(URL_TIMESTAMP), url_name='sets'
    )
    def get_sets(self, request, timestamp_start=None, timestamp_end=None):
        if request.parser_context["view"].model_class.__name__ == "User":
            validate_request_permissions(request=request)

        queryset, timestamp_end = self._get_queryset_filtered_since_timestamp(
            timestamp_start, timestamp_end
        )

        list_filters_field = {
            field_name: set(queryset.values_list(field_name, flat=True))
            for field_name in self.filterset_fields
        }

        data = {
            'sets': list_filters_field,
            'timestamp_start': timestamp_start or 0.0,
            'timestamp_end': timestamp_end,
        }
        return Response(data)

    def get_list_filters_field(self, queryset):
        fields_and_types = get_fields_and_types_of_model(queryset.model)

        return {
            field_name: fields_and_types[field_name]
            for field_name in self.filterset_fields
        }

    def get_extra_informations(self, queryset):
        _model_class = self.model_class or queryset.model
        extra_info = {
            'model_name': _model_class.__name__,
            'model_verbose_name': _model_class._meta.verbose_name,
            'list_display': self.get_list_display(),
            'list_filter': self.get_list_filters_field(queryset),
            'total_objects_count': queryset.count(),
            'create_url': self.request.build_absolute_uri(
                reverse("{}:{}-list".format(API_NAMESPACE, self.basename))
            ),
        }
        if _model_class.__name__ == 'User':
            extra_info['create_url'] = self.request.build_absolute_uri(
                reverse("{}:register-view".format(API_NAMESPACE))
            )
        return extra_info


class TwoFactorLoginView(generics.GenericAPIView):
    """this view is used to login the user"""

    #: Serializer
    serializer_class = TwoFactorLoginSerializer
    api_namespace = API_NAMESPACE

    def post(self, request, *args, **kwargs):
        serializer = TwoFactorLoginSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                data=serializer.errors, status=HTTP_400_BAD_REQUEST
            )

        email = serializer.validated_data["email"]

        ip = get_client_ip(request)
        now = pendulum.now('utc').format(settings.LOGGING['datefmt'])
        user = self.request.user
        base_message = f"[{now}|{ip}|{user}|AUTH] "

        try:
            user = UserModel.objects.get(email=email.lower())
        except ObjectDoesNotExist:
            log_request = (
                base_message
                + f"Connection attempt to unknown user {email} using MFA"
            )
            logger_api_auth.info(log_request)
            return Response(
                data={
                    'message': 'Wrong auth credentials',
                    "_errors": ["WRONG_AUTH_CREDENTIALS"],
                },
                status=HTTP_401_UNAUTHORIZED,
            )
        expire_temporary_tokens(user)
        temp_token = user.temporary_tokens.filter(
            key=serializer.validated_data["token"]
        ).first()
        if not temp_token:
            log_request = (
                base_message + f"Invalid code when validating MFA for {email}"
            )
            logger_api_auth.info(log_request)
            return Response(
                data={
                    'message': 'MFA temporary token invalid',
                    "_errors": ["MFA_TEMP_TOKEN_INVALID"],
                },
                status=HTTP_401_UNAUTHORIZED,
            )
        if temp_token.expired is True:
            log_request = base_message + f"MFA temporary token expired {email}"
            logger_api_auth.info(log_request)
            return Response(
                data={
                    'message': 'MFA temporary token expired',
                    "_errors": ["MFA_TEMP_TOKEN_EXPIRED"],
                },
                status=HTTP_401_UNAUTHORIZED,
            )
        email_device = user.emaildevice_set.filter(confirmed=True).first()

        verified = email_device.verify_token(
            token=serializer.validated_data["verification_code"]
        )
        if not verified:
            log_request = (
                base_message
                + f"Connection attempt to user {email} with wrong MFA code"
            )
            logger_api_auth.info(log_request)
            return Response(
                data={
                    'message': 'Wrong verification code',
                    "_errors": ["WRONG_VERIFICATION_CODE"],
                },
                status=HTTP_401_UNAUTHORIZED,
            )

        # Expire the token to use it only once
        temp_token.expired = True
        temp_token.save()
        serializer = UserSerializer(
            instance=user,
            api_namespace=self.api_namespace,
            context={'is_verified': True},
        )
        log_request = (
            base_message
            + f"Connection attempt to user {email} using MFA is successful"
        )
        logger_api_auth.info(log_request)
        return Response(data=serializer.data, status=HTTP_200_OK)


class AccountMeApiView(ApiV1AccountMeApiView):
    def get_serializer_class(self):
        return make_account_me_serialier(self.api_namespace)


class EmailDeviceAuthView(PaginatedViewSet, viewsets.ModelViewSet):
    authentication_classes = (
        authentication.BasicAuthentication,
        authentication.SessionAuthentication,
        TokenExpiryAuthentication,
        URLTokenExpiryAuthentication,
    )
    model_class = EmailDevice
    permission_classes = (IsAuthenticated,)
    serializer_class = EmailDeviceSerializer
    filterset_fields = ('confirmed', 'email', 'user')

    def get_queryset(self):
        user = self.request.user
        # Return all Email device if at least admin
        # Else, only the user email device
        at_least_admin = False if user.is_anonymous else user.is_at_least_admin
        if at_least_admin:
            return EmailDevice.objects.all()
        else:
            return EmailDevice.objects.filter(user=user)

    def get_extra_informations(self, queryset):
        _model_class = queryset.model
        return {
            'model_name': _model_class.__name__,
            'model_verbose_name': _model_class._meta.verbose_name,
            'total_objects_count': queryset.count(),
            'create_url': self.request.build_absolute_uri(
                reverse("{}:{}-list".format(API_NAMESPACE, self.basename))
            ),
        }

    def perform_create(self, serializer):

        attrs = {'created_by': self.request.user, 'user': self.request.user}
        serializer.save(**attrs)


class ConcreteRoleApiView(PaginatedViewSet, viewsets.ModelViewSet):

    model_class = ConcreteRole
    permission_classes = (IsAuthenticated, ConcreteRolesPermission)
    api_namespace = DEFAULT_API_NAMESPACE
    serializer_class = ConcreteRoleSerializer

    def get_extra_informations(self, queryset):
        _model_class = self.model_class or queryset.model
        return {
            'model_name': _model_class.__name__,
            'model_verbose_name': _model_class._meta.verbose_name,
            'list_display': ['name'],
            'list_filter': {},
            'total_objects_count': queryset.count(),
            'create_url': self.request.build_absolute_uri(
                reverse("{}:{}-list".format(API_NAMESPACE, self.basename))
            ),
        }

    def get_queryset(self):
        return ConcreteRole.objects.all()

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        if isinstance(instance, UserModel):
            request_user = request.user
            at_least_admin = request_user.is_at_least_admin
            if not at_least_admin:
                return Response(status=HTTP_403_FORBIDDEN)
        return super(ConcreteRoleApiView, self).update(
            request, *args, **kwargs
        )

    def perform_create(self, serializer):
        attrs = {'created_by': self.request.user}
        serializer.save(**attrs)


class ConcretePermissionApiView(
    PaginatedViewSet,
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):

    model_class = ConcretePermission
    permission_classes = (IsAuthenticated, ConcreteRolesPermission)
    serializer_class = ConcretePermissionSerializer

    def get_extra_informations(self, queryset):
        _model_class = self.model_class or queryset.model
        return {
            'model_name': _model_class.__name__,
            'model_verbose_name': _model_class._meta.verbose_name,
            'list_display': ['model_name'],
            'list_filter': {},
            'total_objects_count': queryset.count(),
            'create_url': self.request.build_absolute_uri(
                reverse("{}:{}-list".format(API_NAMESPACE, self.basename))
            ),
        }

    def get_queryset(self):
        return ConcretePermission.objects.all()

    def perform_create(self, serializer):
        attrs = {'created_by': self.request.user}
        serializer.save(**attrs)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        if isinstance(instance, UserModel):
            request_user = request.user
            at_least_admin = request_user.is_at_least_admin
            if not at_least_admin:
                return Response(status=HTTP_403_FORBIDDEN)
        return super(ConcretePermissionApiView, self).update(
            request, *args, **kwargs
        )


for meta_model in list_of_meta:
    if meta_model.get_model_name() in ["EntityDividerModel", "UndividedModel"]:
        continue

    permissions_classes = get_permissions_classes_by_meta_model(meta_model)

    viewset_name = '{}ModelViewSet'.format(meta_model.get_model_name())

    if meta_model.get_model_name() == 'User':
        blocked_user_super_cls = make_api_viewset(
            meta_model=meta_model,
            permission_classes=(BlockedUsersPermission,),
            api_model_view_set_class=ApiModelViewSet,
            api_namespace=API_NAMESPACE,
            make_serializer_class_fct=make_serializer_class,
        )

        def get_blocked_queryset(self):
            user = self.request.user
            at_least_staff = (
                False if user.is_anonymous else user.is_at_least_staff
            )

            #: Anonymous user can only see public objects
            user_filters = {'is_active': False}
            if not at_least_staff:
                user_filters.update(public=True)
            return UserModel.objects.filter(**user_filters)

        extra_attrs = {
            'post': unauthorized,
            'update': unauthorized,
            'get_queryset': get_blocked_queryset,
        }
        blocked_user_view_cls = type(
            'BlockedUsersApiViewset', (blocked_user_super_cls,), extra_attrs
        )
        setattr(
            sys.modules[__name__],
            'BlockedUsersApiViewset',
            blocked_user_view_cls,
        )

    setattr(
        sys.modules[__name__],
        viewset_name,
        make_api_viewset(
            meta_model=meta_model,
            permission_classes=permissions_classes,
            api_model_view_set_class=ApiModelViewSet,
            api_namespace=API_NAMESPACE,
            make_serializer_class_fct=make_serializer_class,
        ),
    )


def make_deprecated_viewset(viewset, correct_url):
    class DeprecatedViewSet(viewset):
        def list(self, *args, **kwargs):
            warning_message = (
                "This route will be depricated in the next version of "
                f"concrete datastore. Please use '{correct_url}' instead"
            )
            warnings.warn(warning_message, DeprecationWarning)
            try:
                return super().list(*args, **kwargs)
            except AttributeError:
                return HttpResponseNotAllowed(self.request.method)

        def get_object(self, *args, **kwargs):
            warning_message = (
                "This route will be depricated in the next version of "
                f"concrete datastore. Please use '{correct_url}' instead"
            )
            warnings.warn(warning_message, DeprecationWarning)
            try:
                return super().get_object(*args, **kwargs)
            except AttributeError:
                return HttpResponseNotAllowed(self.request.method)

        def create(self, *args, **kwargs):
            warning_message = (
                "This route will be depricated in the next version of "
                f"concrete datastore. Please use '{correct_url}' instead"
            )
            warnings.warn(warning_message, DeprecationWarning)
            try:
                return super().create(*args, **kwargs)
            except AttributeError:
                return HttpResponseNotAllowed(self.request.method)

        def destroy(self, *args, **kwargs):
            warning_message = (
                "This route will be depricated in the next version of "
                f"concrete datastore. Please use '{correct_url}' instead"
            )
            warnings.warn(warning_message, DeprecationWarning)
            try:
                return super().destroy(*args, **kwargs)
            except AttributeError:
                return HttpResponseNotAllowed(self.request.method)

    return DeprecatedViewSet


class UnBlockUsersApiViewset(generics.GenericAPIView):
    serializer_class = BlockedUserUpdateSerializer
    authentication_classes = (
        authentication.SessionAuthentication,
        TokenExpiryAuthentication,
        URLTokenExpiryAuthentication,
    )
    permission_classes = (BlockedUsersPermission,)
    model_class = UserModel

    def get_serializer_class(self):
        return self.serializer_class

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = self.unblock_users(serializer.data['user_uids'])
        return Response(data, status=status.HTTP_200_OK)

    def unblock_users(self, user_uids):
        #:  if one or more uids is not found or is not in queryset, raise 404
        for user_uid in user_uids:
            user = get_object_or_404(UserModel, pk=user_uid)

        data = {}
        for user_uid in user_uids:
            user = UserModel.objects.get(pk=user_uid)
            if user.is_active:
                data[user_uid] = 'User is already active'
                continue
            user.set_level('simpleuser', commit=True)
            data[user_uid] = 'User successfully unblocked'
        return data
