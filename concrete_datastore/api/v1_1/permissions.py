# coding: utf-8
from django.conf import settings

from rest_framework.exceptions import APIException
from rest_framework import permissions, status


class PreconditionFailed(APIException):
    status_code = status.HTTP_412_PRECONDITION_FAILED
    default_detail = 'Precondition Fail to perform this action'
    default_code = 'precondition_failed'


CONCRETE_SETTINGS = getattr(settings, 'CONCRETE', {})
API_PERMISSIONS_CLASSES = CONCRETE_SETTINGS.get('API_PERMISSIONS_CLASSES', {})


def check_minimum_level(method, user, model):
    authenticated = user.is_authenticated
    superuser = user.is_superuser is True
    at_least_admin = False if user.is_anonymous else user.is_at_least_admin
    staff = False if user.is_anonymous else user.is_at_least_staff
    at_least_anonymous = True  #: Always true

    # Set minimum level to do operations on ConcreteRole models
    METHOD_TO_MINIMUM_LEVEL_NAME = {
        'GET': 'authenticated',
        'POST': 'admin',
        'PUT': 'admin',
        'PATCH': 'admin',
        'DELETE': 'admin',
    }

    PERMISSION_LEVELS = {
        'superuser': superuser,
        'admin': at_least_admin,
        'staff': staff,
        'manager': staff,
        'authenticated': authenticated,
        'anonymous': at_least_anonymous,
    }

    level_value = METHOD_TO_MINIMUM_LEVEL_NAME[method]
    user_allowed = PERMISSION_LEVELS[level_value]
    return user_allowed


class BlockedUsersPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        user = request.user
        if not user.is_anonymous:
            if not user.is_confirmed():
                raise PreconditionFailed(
                    detail={
                        'message': 'Email has not been validated',
                        "_errors": ["EMAIL_NOT_VALIDATED"],
                    }
                )
        if request.method not in ["OPTIONS", "HEAD"]:
            if user.is_anonymous:
                return False
            return user.is_at_least_admin
        return True


class ConcreteRolesPermission(permissions.BasePermission):
    message = 'User access permission refused.'

    # Permissions linked to ConcreteRole and ConcretePermission views
    def has_permission(self, request, view):
        if not request.user.is_anonymous:
            if not request.user.is_confirmed():
                raise PreconditionFailed(
                    detail={
                        'message': 'Email has not been validated',
                        "_errors": ["EMAIL_NOT_VALIDATED"],
                    }
                )
        if request.method not in ["OPTIONS", "HEAD"]:
            model = view.model_class
            level_allowed = check_minimum_level(
                request.method, request.user, model
            )
            return level_allowed
        return True
