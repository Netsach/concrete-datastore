# coding: utf-8
from functools import update_wrapper

from django.urls import reverse
from django.conf import settings
from django.contrib.admin.sites import AdminSite
from django_otp.admin import OTPAdminSite

from concrete_datastore.admin.admin_form import (
    MyAuthForm,
    OTPAuthenticationForm,
)

EXTRA_MODEL_OBJECT_NAMES = ('Email',)
AUTH_MODEL_OBJECT_NAMES = (
    'User',
    'Group',
    'AuthToken',
    'ConcretePermission',
    'ConcreteRole',
)


def get_admin_site():
    if settings.USE_TWO_FACTOR_AUTH:
        admin_site = OTPAdminSite
        admin_site_kwargs = {'name': 'admin'}
        login_template = "admin/mfa-login.html"
        login_form = OTPAuthenticationForm
    else:
        admin_site = AdminSite
        admin_site_kwargs = {}
        login_template = "admin/login.html"
        login_form = MyAuthForm

    class CustomAdminSite(admin_site):
        def get_urls(self):
            from django.urls import include, path, re_path

            # Since this module gets imported in the application's root package,
            # it cannot import models from other applications at the module level,
            # and django.contrib.contenttypes.views imports ContentType.
            from django.contrib.contenttypes import views as contenttype_views

            def wrap(view, cacheable=False):
                def wrapper(*args, **kwargs):
                    return self.admin_view(view, cacheable)(*args, **kwargs)

                wrapper.admin_site = self
                return update_wrapper(wrapper, view)

            # Admin-site-wide views.
            urlpatterns = [
                path('', wrap(self.index), name='index'),
                path('login/', self.login, name='login'),
                path('logout/', wrap(self.logout), name='logout'),
                path(
                    'password_change/',
                    wrap(self.password_change, cacheable=True),
                    name='password_change',
                ),
                path(
                    'password_change/done/',
                    wrap(self.password_change_done, cacheable=True),
                    name='password_change_done',
                ),
                path(
                    'jsi18n/',
                    wrap(self.i18n_javascript, cacheable=True),
                    name='jsi18n',
                ),
                path(
                    'r/<int:content_type_id>/<path:object_id>/',
                    wrap(contenttype_views.shortcut),
                    name='view_on_site',
                ),
            ]

            # Add in each model's views, and create a list of valid URLS for the
            # app_index
            valid_app_labels = []
            for model, model_admin in self._registry.items():
                urlpatterns += [
                    path(
                        '%s/' % (model._meta.model_name),
                        include(model_admin.urls),
                    )
                ]
                if model._meta.app_label not in valid_app_labels:
                    valid_app_labels.append(model._meta.app_label)

            # If there were ModelAdmins registered, we should have a list of app
            # labels for which we need to allow access to the app_index view,
            if valid_app_labels:
                regex = r'^(?P<app_label>' + '|'.join(valid_app_labels) + ')/$'
                urlpatterns += [
                    re_path(regex, wrap(self.app_index), name='app_list')
                ]

            return urlpatterns

        def get_app_list(self, request):
            app_dict = self._build_app_dict(request)
            if not app_dict:
                return []
            # Sort the apps alphabetically.
            app_list = sorted(
                app_dict.values(), key=lambda x: x['name'].lower()
            )

            # Sort the models alphabetically within each app.
            for app in app_list:
                app['models'].sort(key=lambda x: x['name'])
            concrete_app_filter = filter(
                lambda x: x['app_label'].lower() == 'concrete', app_list
            )
            concrete_app = next(concrete_app_filter)
            models = concrete_app.pop('models')
            model_group_models = {
                'group_name': 'Models',
                **concrete_app,
                'models': [
                    model
                    for model in models
                    if model['object_name']
                    not in EXTRA_MODEL_OBJECT_NAMES + AUTH_MODEL_OBJECT_NAMES
                ],
            }
            extra_group_models = {
                'group_name': 'Extra',
                **concrete_app,
                'models': [
                    model
                    for model in models
                    if model['object_name'] in EXTRA_MODEL_OBJECT_NAMES
                ],
            }
            auth_group_models = {
                'group_name': 'Auth',
                **concrete_app,
                'models': [
                    model
                    for model in models
                    if model['object_name'] in AUTH_MODEL_OBJECT_NAMES
                ],
            }
            custom_app_groups_list = [
                auth_group_models,
                extra_group_models,
                model_group_models,
            ]
            return custom_app_groups_list

        def index(self, request, extra_context=None, *args, **kwargs):
            if settings.USE_CORE_AUTOMATION:
                extra_context = {
                    'use_core_automation': True,
                    'target_admin_view': reverse('coreAdmin:index'),
                    'target_admin_view_name': 'Core Admin',
                }
            return super().index(request, extra_context, *args, **kwargs)

    CustomAdminSite.login_template = login_template
    CustomAdminSite.login_form = login_form

    return CustomAdminSite(
        **admin_site_kwargs  # pylint: disable = unexpected-keyword-arg
    )
