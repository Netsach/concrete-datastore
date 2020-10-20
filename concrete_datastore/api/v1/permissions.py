# coding: utf-8
from importlib import import_module

from django.db.models import Q
from django.conf import settings
from django.contrib.auth import get_user_model

from rest_framework.exceptions import APIException
from rest_framework import permissions, status

from concrete_datastore.concrete.models import (
    ConcretePermission,
    DIVIDER_MODEL,
    UNDIVIDED_MODEL,
)


DIVIDER_MODELs = "{}s".format(DIVIDER_MODEL)
DIVIDER_MODELs_LOWER = DIVIDER_MODELs.lower()
DIVIDER_MODEL_LOWER = DIVIDER_MODEL.lower()


class PreconditionFailed(APIException):
    status_code = status.HTTP_412_PRECONDITION_FAILED
    default_detail = 'Precondition Fail to perform this action'
    default_code = 'precondition_failed'


CONCRETE_SETTINGS = getattr(settings, 'CONCRETE', {})
API_PERMISSIONS_CLASSES = CONCRETE_SETTINGS.get('API_PERMISSIONS_CLASSES', {})


def get_permissions_classes_by_meta_model(meta_model):
    permissions_classes_path = API_PERMISSIONS_CLASSES.get(
        meta_model._specifier.name,
        ('concrete_datastore.api.v1.permissions.UserAccessPermission',),
    )

    permissions_classes = ()

    for permission_class_path in permissions_classes_path:
        module = import_module(
            permission_class_path[: permission_class_path.rfind('.')]
        )

        try:
            permissions_classes += (
                getattr(module, permission_class_path.split('.')[-1]),
            )
        except AttributeError:
            raise RuntimeError(
                'CONCRETE impoperly configured : unknown '
                'permission class {}'.format(permission_class_path)
            )
    return permissions_classes


def check_minimum_level(method, user, model):
    authenticated = user.is_authenticated
    superuser = user.is_superuser is True
    at_least_admin = False if user.is_anonymous else user.is_at_least_admin
    staff = False if user.is_anonymous else user.is_at_least_staff
    at_least_anonymous = True  #: Always true

    METHOD_TO_LEVEL_NAME = {
        'GET': '__retrieve_minimum_level__',
        'POST': '__creation_minimum_level__',
        'PUT': '__update_minimum_level__',
        'PATCH': '__update_minimum_level__',
        'DELETE': '__delete_minimum_level__',
    }

    PERMISSION_LEVELS = {
        'superuser': superuser,
        'admin': at_least_admin,
        'staff': staff,
        'manager': staff,
        'authenticated': authenticated,
        'anonymous': at_least_anonymous,
    }

    level_name = METHOD_TO_LEVEL_NAME[method]
    level_value = getattr(model, level_name)
    user_allowed = PERMISSION_LEVELS[level_value]
    return user_allowed


def check_roles(method, user, model):
    # Checking roles doesn't applies to admin and SU
    at_least_admin = False if user.is_anonymous else user.is_at_least_admin
    if at_least_admin:
        return True

    allowed = False
    user_roles = user.get_roles()
    permission_model, _ = ConcretePermission.objects.get_or_create(
        model_name=model.__name__
    )

    model_allowed_roles_qs = {
        'GET': permission_model.retrieve_roles,
        'POST': permission_model.create_roles,
        'PUT': permission_model.update_roles,
        'PATCH': permission_model.update_roles,
        'DELETE': permission_model.delete_roles,
    }

    # Filter the queryset corresponding to the method with user's roles
    allowed = (
        model_allowed_roles_qs[method].filter(name__in=user_roles).exists()
    )

    return allowed


def does_intersect(queryset_1, queryset_2):
    if queryset_1.model is not queryset_2.model:
        raise ValueError(
            f"Attempting intersection between two querysets of different models"
        )
    return queryset_1.filter(
        pk__in=queryset_2.values_list('pk', flat=True)
    ).exists()


class UserAccessPermission(permissions.BasePermission):
    message = 'User access permission refused.'

    def check_divider_permission(self, request, obj):
        if obj.__class__.__name__ in UNDIVIDED_MODEL:
            return True
        if obj.__class__.__name__ == DIVIDER_MODEL:
            return (
                getattr(request.user, DIVIDER_MODELs_LOWER)
                .filter(pk=obj.pk)
                .exists()
            )

        if getattr(obj, DIVIDER_MODEL_LOWER) is None:
            return True
        return self.is_obj_divider_accessible_by_user(request, obj)

    def is_obj_divider_accessible_by_user(self, request, obj):
        return (
            getattr(request.user, DIVIDER_MODELs_LOWER)
            .filter(pk=getattr(obj, DIVIDER_MODEL_LOWER).pk)
            .exists()
        )

    def has_permission(self, request, view):
        if not hasattr(view, 'model_class'):
            # Validated by LCO on 2019-05-15
            # In this case, if that ever happened, view should be set to
            # view = request.parser_context["view"]
            raise AttributeError('View has no model_class attr, see comment')
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
            if settings.USE_CONCRETE_ROLES and model != get_user_model():
                roles_allowed = check_roles(
                    request.method, request.user, model
                )
                return level_allowed and roles_allowed
            else:
                return level_allowed

        return True

    def is_field_not_divider_changed(self, request):
        # If a key different of the divider is in the data, data will be changed
        if request.data:
            for key in request.data:
                if key != DIVIDER_MODELs_LOWER:
                    return True
        # If the divider is not in the request data
        return False

    def can_access_user_obj(self, request, user, obj):
        field_not_divider_changed = self.is_field_not_divider_changed(request)
        #: If the obj has a lower level, authorize
        if obj < user:
            return True
        #: If the obj has a greater level, deny
        if obj > user:
            return False
        # If the obj has the same level, check if no data has been changed except divider
        if field_not_divider_changed is False:
            return True
        return False

    def can_delete_user_obj(self, request, user, obj):
        superuser = user.is_superuser is True
        at_least_staff = False if user.is_anonymous else user.is_at_least_staff

        if superuser:
            return True
        # If it at least staff, check levels
        if at_least_staff:
            #: If the obj has a lower level, authorize
            if obj < user:
                return True
            #: If the obj has a greater or equal level, deny
            else:
                return False

        #: If it is not at least staff, deny
        return False

    def has_object_permission(self, request, view, obj):
        user = request.user
        superuser = user.is_superuser is True
        at_least_staff = False if user.is_anonymous else user.is_at_least_staff
        authenticated = user.is_authenticated is True
        if request.method in permissions.SAFE_METHODS:
            return (
                obj.public is True
                or isinstance(obj, get_user_model())
                or authenticated
            )

        elif isinstance(obj, get_user_model()):
            # UPDATE User only if user or superuser
            is_himself = obj.pk == user.pk
            if request.method == 'DELETE':
                return self.can_delete_user_obj(request, user, obj)
            if is_himself:
                return True
            if superuser:
                return True
            elif at_least_staff:
                return self.can_access_user_obj(request, user, obj)
            else:
                return False
        else:
            return authenticated and (
                (obj.created_by is not None and obj.created_by.pk == user.pk)
                or (user.is_at_least_admin)
                or (
                    obj.can_admin_users.filter(pk=user.pk).exists()
                    or does_intersect(
                        obj.can_admin_groups, user.concrete_groups
                    )
                )
                or (
                    at_least_staff
                    and self.check_divider_permission(request, obj) is True
                )
            )


def get_available_scope_pks_for(user):
    all_divider_pk = list(
        set(getattr(user, DIVIDER_MODELs_LOWER).values_list('pk', flat=True))
    )
    return all_divider_pk


def apply_scope_filters(user, queryset):
    model_name = queryset.model.__name__
    model_is_divided = model_name not in UNDIVIDED_MODEL
    if not model_is_divided:
        return queryset.none()

    divider_query = "{}__pk__in".format(DIVIDER_MODEL_LOWER)
    all_divider_pk = get_available_scope_pks_for(user)
    return queryset.filter(**{divider_query: all_divider_pk})


def filter_queryset_by_divider(queryset, user, divider):
    """
    queryset is the one of the current view,
    user is the connected one or anonymous
    divider is the one in headers and guarantee that current model is divided
    """
    if divider is None:
        raise ValueError("The divider should not be null")

    # On check en premier le divider
    queryset = queryset.filter(**{DIVIDER_MODEL_LOWER: divider.uid})

    if user.is_superuser is True:
        return queryset
    elif getattr(user, 'admin', False) is True:
        return queryset

    # Authenticated users
    if user.is_authenticated is True:
        queryset = apply_scope_filters(user, queryset)

    return queryset


def filter_queryset_by_permissions(queryset, user, divider):
    if queryset.model == get_user_model():
        raise ValueError(
            "Queryset of model User cannot be filtered by permissions"
        )
    all_public = Q(public=True)

    #: Anonymous user can only see public objects
    if user.is_authenticated is not True:
        return queryset.filter(all_public)

    # OBSOLETE RIGHT NOW
    # SHOULD BE DISCUSSED
    #: If current user a "local administrator" on the divided model
    # try:
    #     if getattr(
    #         user, DIVIDER_MODELs_LOWER
    #     ).filter(divider_admin=True).exists():
    #         return queryset
    # except Exception:
    #     #: Pass explicit
    #     pass

    all_owned = Q(created_by__pk=user.pk)
    all_administrables = Q(can_admin_users__pk=user.pk)
    all_viewables = Q(can_view_users__pk=user.pk)
    all_group_viewables = Q(
        can_view_groups__pk__in=user.concrete_groups.values_list(
            'pk', flat=True
        )
    )
    all_group_administrables = Q(
        can_admin_groups__pk__in=user.concrete_groups.values_list(
            'pk', flat=True
        )
    )
    filterd_queryset = queryset.filter(
        all_public
        | all_owned
        | all_administrables
        | all_viewables
        | all_group_viewables
        | all_group_administrables
    )
    #: Segment data per user level
    if user.is_superuser is True:
        return queryset
    elif getattr(user, 'admin', False) is True:
        return queryset
    elif user.is_staff is True:
        #: Objects that should be returned must have a FK (from the scoping
        #: relation) towards the scope model *instances* (formerly named divider)
        queryset = (
            apply_scope_filters(user, queryset) | filterd_queryset
        ).distinct()
        return queryset
    else:
        queryset = filterd_queryset
        #: Here we may have redundant objects, apply distinct on queryset
        #: May be unsupported by sqlite
        queryset = queryset.distinct()

    return queryset
