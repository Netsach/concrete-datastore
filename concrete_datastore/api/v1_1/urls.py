# coding: utf-8
from django.urls import re_path
from django.conf import settings

from rest_framework.routers import SimpleRouter

from concrete_datastore.concrete.meta import list_of_meta
from concrete_datastore.api.v1.views import (
    LoginApiView,
    RegisterApiView,
    ResetPasswordApiView,
    ChangePasswordView,
    RetrieveSecureTokenApiView,
    SecureLoginApiView,
    GenerateSecureTokenApiView,
)
from concrete_datastore.api.v1_1.views import (  # pylint:disable=E0611
    ConcreteRoleApiView,
    ConcretePermissionApiView,
    EmailDeviceAuthView,
    LDAPLoginApiView,
    TwoFactorLoginView,
    UnBlockUsersApiViewset,
    BlockedUsersApiViewset,
    AccountMeApiView,
    ProcessRegisterApiView,
)
from concrete_datastore.api.v1_1 import views, API_NAMESPACE

app_name = 'concrete_datastore.concrete'

# API Front end
router = SimpleRouter()

for meta_model in list_of_meta:
    if meta_model.get_model_name() in ["EntityDividerModel", "UndividedModel"]:
        continue

    viewset = getattr(
        views, '{}ModelViewSet'.format(meta_model.get_model_name())
    )

    router.register(
        prefix=meta_model.get_dashed_case_class_name(),
        viewset=viewset,
        basename=meta_model.get_dashed_case_class_name(),
    )


router.register(
    prefix='acl/role', viewset=ConcreteRoleApiView, basename='acl-role'
)
router.register(
    prefix='acl/permission',
    viewset=ConcretePermissionApiView,
    basename='acl-permission',
)
router.register(
    prefix='blocked-users',
    viewset=BlockedUsersApiViewset,
    basename='blocked-users',
)

router.register(
    prefix='email-device', viewset=EmailDeviceAuthView, basename='email-device'
)

specific_urlpatterns = [
    re_path(
        r'^auth/ldap/login', LDAPLoginApiView.as_view(), name='login-ldap-view'
    ),
    re_path(
        r'auth/two-factor/login',
        TwoFactorLoginView.as_view(),
        name='two-factor-login',
    ),
    re_path(
        r'^auth/login/',
        LoginApiView.as_view(api_namespace=API_NAMESPACE),
        name='login-view',
    ),
    re_path(
        r'^auth/register/',
        RegisterApiView.as_view(api_namespace=API_NAMESPACE),
        name='register-view',
    ),
    re_path(
        r'^account/me/',
        AccountMeApiView.as_view(api_namespace=API_NAMESPACE),
        name='account-me',
    ),
    re_path(
        r'^auth/change-password/',
        ChangePasswordView.as_view(api_namespace=API_NAMESPACE),
        name='change-password',
    ),
    re_path(
        r'^auth/reset-password/',
        ResetPasswordApiView.as_view(),
        name='reset-password',
    ),
    re_path(
        r'secure-connect/retrieve-token',
        RetrieveSecureTokenApiView.as_view(),
        name='retrieve-secure-token',
    ),
    re_path(
        r'secure-connect/login/',
        SecureLoginApiView.as_view(api_namespace=API_NAMESPACE),
        name='secure-connect-login',
    ),
    re_path(
        r'secure-connect/generate-token',
        GenerateSecureTokenApiView.as_view(),
        name='generate-secure-token',
    ),
    re_path(
        r'process/register/',
        ProcessRegisterApiView.as_view(),
        name='register-as-process',
    ),
    re_path(
        r'unblock-users',
        UnBlockUsersApiViewset.as_view(),
        name='unblock-users',
    ),
]
if settings.USE_AUTH_LDAP:
    specific_urlpatterns += [
        re_path(
            r'^auth/ldap/login',
            LDAPLoginApiView.as_view(),
            name='login-ldap-view',
        )
    ]


urlpatterns = router.urls + specific_urlpatterns
