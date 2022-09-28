# coding: utf-8
from __future__ import (
    absolute_import,
    division,
    print_function,
    unicode_literals,
)
import pendulum
from django_otp.middleware import OTPMiddleware
from concrete_datastore.api.v1.datetime import format_datetime
from concrete_datastore.concrete.models import EmailDevice


class OTPCustomMiddleware(OTPMiddleware):
    def _device_from_persistent_id(self, persistent_id):
        if persistent_id.count('.') > 1:
            parts = persistent_id.split('.')
            persistent_id = '.'.join((parts[-3], parts[-1]))

        device = EmailDevice.from_persistent_id(persistent_id)

        return device


class DateTimeLoggerMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        date_received = pendulum.now('utc')
        response = self.get_response(request)
        date_sent = pendulum.now('utc')
        response['DateTime-Received'] = format_datetime(date_received)
        response['DateTime-Sent'] = format_datetime(date_sent)
        return response
