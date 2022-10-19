# coding: utf-8
from django.urls import re_path
from django.conf import settings

from concrete_datastore.concrete.views import email_confirmation_view
from concrete_datastore.concrete.views import unsubscribe_notifications_view
from concrete_datastore.concrete.views import (
    unsubscribe_notifications_result_view,
    dump_data,
    load_data,
)

app_name = 'concrete_datastore.concrete'

urlpatterns = [
    re_path(
        r'^confirm-user-email/(?P<token>[-\w]+)',
        email_confirmation_view,
        name='email_confirmation',
    ),
    re_path(
        r'^unsubscribe-notifications/(?P<token>[-\w]+)',
        unsubscribe_notifications_view,
        name='unsubscribe_notifications',
    ),
    re_path(
        r'^unsubscribe-notifications-result/(?P<token>[-\w]+)',
        unsubscribe_notifications_result_view,
        name='unsubscribe_notifications_result',
    ),
]

if settings.ENABLE_DATABASE_DUMP:
    urlpatterns.append(re_path(r'dump-data', dump_data, name="dump_data"))
if settings.ENABLE_DATABASE_LOAD:
    urlpatterns.append(re_path(r'load-data', load_data, name="load_data"))
