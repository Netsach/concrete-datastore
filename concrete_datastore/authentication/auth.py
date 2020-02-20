# coding: utf-8
import logging

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend


UserModel = get_user_model()
logger = logging.getLogger('authentication')


class ConcreteBackend(ModelBackend):
    def authenticate(
        self, request=None, username=None, password=None, **kwargs
    ):
        user = super(ConcreteBackend, self).authenticate(
            request=request, username=username, password=password, **kwargs
        )

        if user is not None:
            if kwargs.get('from_api', False):
                return user
            if self.user_can_authenticate_to_backend(user):
                return user
        return None

    def user_can_authenticate_to_backend(self, user):
        minimum_backend_auth_level = getattr(
            settings, 'MINIMUM_BACKEND_AUTH_LEVEL', 'is_superuser'
        )

        return getattr(user, minimum_backend_auth_level, False) is True
