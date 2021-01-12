# coding: utf-8
from django.urls import re_path, include
from django.conf import settings
from django.views.static import serve
from django.views.generic import TemplateView
from concrete_datastore.admin.admin import admin_site
from .views import service_status_view, OpenApiView

app_name = 'concrete_datastore.concrete'

api_v1_1_urls = re_path(
    r'^api/v1\.1/',
    include('concrete_datastore.api.v1_1.urls', namespace='api_v1_1'),
)
api_v1_urls = re_path(
    r'^api/v1/', include('concrete_datastore.api.v1.urls', namespace='api_v1')
)

swagger_urls = [
    re_path(
        r'openapi-schema\.(?P<spec_format>json|yaml)$',
        OpenApiView.as_view(patterns=[api_v1_1_urls]),
        name='openapi-schema',
    ),
    re_path(
        r'^swagger-ui/',
        TemplateView.as_view(
            template_name='mainApp/swagger-ui.html',
            extra_context={'schema_url': 'openapi-schema'},
        ),
        name='swagger-ui',
    ),
]

urlpatterns = [
    re_path(r'^oauth/', include('social_django.urls', namespace='social')),
    re_path(r'^status/$', service_status_view, name='service-status-view'),
    re_path(
        r'^c/',
        include('concrete_datastore.concrete.urls', namespace='concrete'),
    ),
    api_v1_urls,
    api_v1_1_urls,
    *swagger_urls,
]
if settings.ADMIN_URL_ENABLED:
    urlpatterns += [
        re_path(rf'^{settings.ADMIN_ROOT_URI}/', admin_site.urls, name='admin')
    ]

if settings.DEBUG:
    try:
        import debug_toolbar

        urlpatterns += [re_path(r'^__debug__/', include(debug_toolbar.urls))]
    except ImportError:
        # Ignore debug_toolbar if not installed
        pass

    urlpatterns += [
        re_path(
            r'^m/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}
        ),
        re_path(
            r'^s/(?P<path>.*)$', serve, {'document_root': settings.STATIC_ROOT}
        ),
    ]
if settings.USE_CORE_AUTOMATION:
    # ImportError if the import fails
    import ns_core  # pylint: disable = import-error
    from ns_core.coreApp.admin_site import (  # pylint: disable = import-error
        admin_site as core_admin_site,
    )

    urlpatterns += [
        re_path(r'^core/', include('ns_core.coreApp.urls', namespace='')),
        re_path(r'^core-admin/', core_admin_site.urls, name='core-admin'),
    ]


urlpatterns += [
    re_path(
        r'^$',
        TemplateView.as_view(template_name='mainApp/index.html'),
        name='index',
    ),
    re_path(
        r'^oauth-logged$',
        TemplateView.as_view(template_name='mainApp/logged-using-oauth.html'),
        name='index-logged',
    ),
]
