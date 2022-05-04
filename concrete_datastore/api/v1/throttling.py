from django.conf import settings
from rest_framework.throttling import UserRateThrottle, AnonRateThrottle
from django.contrib.auth.models import AbstractUser, AnonymousUser


class CustomUserRateThrottle(UserRateThrottle):
    def get_cache_key(self, request, view):
        if settings.ENABLE_AUTHENTICATED_USER_THROTTLING is False:
            return None
        user = request.user
        if not isinstance(user, (AbstractUser, AnonymousUser)):
            return None
        if user.is_authenticated:
            return user.email
        return None

    def get_rate(self):
        return settings.USER_THROTTLING_RATE


class CustomAnonymousRateThrottle(AnonRateThrottle):
    def get_cache_key(self, request, view):
        if settings.ENABLE_ANONYMOUS_USER_THROTTLING is False:
            return None
        user = request.user
        if not isinstance(user, (AbstractUser, AnonymousUser)):
            return None

        if user.is_authenticated:
            return None
        return super().get_cache_key(request, view)

    def get_rate(self):
        return settings.ANONYMOUS_THROTTLING_RATE
