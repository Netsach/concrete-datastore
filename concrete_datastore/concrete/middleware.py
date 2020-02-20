# coding: utf-8
from __future__ import (
    absolute_import,
    division,
    print_function,
    unicode_literals,
)

from django_otp.middleware import OTPMiddleware

from concrete_datastore.concrete.models import EmailDevice


class OTPCustomMiddleware(OTPMiddleware):
    def _device_from_persistent_id(self, persistent_id):
        if persistent_id.count('.') > 1:
            parts = persistent_id.split('.')
            persistent_id = '.'.join((parts[-3], parts[-1]))

        device = EmailDevice.from_persistent_id(persistent_id)

        return device
