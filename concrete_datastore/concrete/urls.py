# coding: utf-8
from django.urls import re_path

from concrete_datastore.concrete.views import email_confirmation_view
from concrete_datastore.concrete.views import unsubscribe_notifications_view
from concrete_datastore.concrete.views import (
    unsubscribe_notifications_result_view,
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
