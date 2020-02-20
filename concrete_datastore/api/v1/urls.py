# coding: utf-8
from django.urls import re_path

from rest_framework.routers import SimpleRouter

from concrete_datastore.concrete.meta import list_of_meta
from concrete_datastore.api.v1.signals import send_email
from concrete_datastore.api.v1.views import (
    LoginApiView,
    RegisterApiView,
    ResetPasswordApiView,
    ChangePasswordView,
    AccountMeApiView,
    RetrieveSecureTokenApiView,
    SecureLoginApiView,
    GenerateSecureTokenApiView,
)
from concrete_datastore.api.v1 import views, DEFAULT_API_NAMESPACE

app_name = 'concrete_datastore.concrete'

if not callable(send_email):
    raise ValueError("The method used to send emails should be a callable")

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


specific_urlpatterns = [
    re_path(
        r'^auth/login/',
        LoginApiView.as_view(api_namespace=DEFAULT_API_NAMESPACE),
        name='login-view',
    ),
    re_path(
        r'^auth/register/',
        RegisterApiView.as_view(api_namespace=DEFAULT_API_NAMESPACE),
        name='register-view',
    ),
    re_path(
        r'^account/me/',
        AccountMeApiView.as_view(api_namespace=DEFAULT_API_NAMESPACE),
        name='account-me',
    ),
    re_path(
        r'^auth/change-password/',
        ChangePasswordView.as_view(api_namespace=DEFAULT_API_NAMESPACE),
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
        SecureLoginApiView.as_view(api_namespace=DEFAULT_API_NAMESPACE),
        name='secure-connect-login',
    ),
    re_path(
        r'secure-connect/generate-token',
        GenerateSecureTokenApiView.as_view(),
        name='generate-secure-token',
    ),
]

urlpatterns = router.urls + specific_urlpatterns
