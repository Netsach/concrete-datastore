# coding: utf-8
from importlib import import_module
import logging
import warnings
from copy import deepcopy
from django.db.models import Q
from django.conf import settings
from django.contrib.auth import get_user_model

from rest_framework.exceptions import APIException
from rest_framework import permissions, status
from concrete_datastore.concrete.models import (
    ConcretePermission,
    InstancePermission,
    DIVIDER_MODEL,
    UNDIVIDED_MODEL,
)

logger = logging.getLogger(__name__)

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


class UserAtLeastAuthenticatedPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.user.is_anonymous:
            return False
        return super().has_permission(request, view)


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
        model = view.model_class
        if model == get_user_model():
            if request.user.is_anonymous or not request.user.is_at_least_staff:
                return False

        if request.method not in ["OPTIONS", "HEAD"]:
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
            if authenticated is False:
                return False
            if user.is_at_least_admin:
                return True

            try:
                model_name = obj._meta.model.__name__
                instance_permissions = InstancePermission.objects.get(
                    user_id=user.pk, model_name=model_name
                )
            except InstancePermission.DoesNotExist:
                return False
            return str(obj.pk) in instance_permissions.write_instance_uids


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
    warnings.warn(
        'The method "filter_queryset_by_permissions" is deprecated',
        DeprecationWarning,
    )
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
    warnings.warn(
        'The method "filter_queryset_by_permissions" is deprecated',
        DeprecationWarning,
    )
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


def filter_queryset_by_permissions_and_scope(queryset, user, divider=None):
    if user.is_anonymous:
        return queryset.filter(public=True)
    model_name = queryset.model.__name__
    kwargs = {}
    if divider is not None:
        kwargs[DIVIDER_MODEL_LOWER] = divider
    if user.is_authenticated and user.is_at_least_admin:
        qs = queryset
    else:
        try:
            instance_permission = user.instance_permissions.get(
                model_name=model_name
            )
            filters = Q(pk__in=instance_permission.read_instance_uids) | Q(
                public=True
            )
        except InstancePermission.DoesNotExist:
            filters = Q(public=True)
        qs = queryset.filter(filters)
    if user.is_at_least_staff:
        model_is_divided = model_name not in UNDIVIDED_MODEL
        if model_is_divided:
            divider_query = "{}_id__in".format(DIVIDER_MODEL_LOWER)
            all_divider_pk = get_available_scope_pks_for(user)
            qs |= queryset.filter(**{divider_query: all_divider_pk})

    return qs.filter(**kwargs)


def get_read_write_permission_users(
    user,
    instances_qs,
    user_groups_pks,
    include_divider=True,
    include_view_groups=True,
    include_admin_groups=True,
    include_view_users=True,
    include_admin_users=True,
):
    user_id = user.pk
    created_by_qs = instances_qs.filter(created_by_id=user_id).values_list(
        'pk', flat=True
    )
    can_view_users_qs = instances_qs.filter(
        can_view_users__pk=user_id
    ).values_list('pk', flat=True)
    can_view_groups_qs = instances_qs.filter(
        can_view_groups__pk__in=user_groups_pks
    ).values_list('pk', flat=True)

    can_admin_users_qs = instances_qs.filter(
        can_admin_users__pk=user_id
    ).values_list('pk', flat=True)
    can_admin_groups_qs = instances_qs.filter(
        can_admin_groups__pk__in=user_groups_pks
    ).values_list('pk', flat=True)
    write_instances_uids = created_by_qs

    if include_admin_groups is True:
        write_instances_uids = write_instances_uids.union(can_admin_groups_qs)

    if include_admin_users is True:
        write_instances_uids = write_instances_uids.union(can_admin_users_qs)

    #: A manager has write permissions on his scope
    model_name = instances_qs.model.__name__
    if (
        (user.is_at_least_staff is True)
        and (model_name not in UNDIVIDED_MODEL)
        and (include_divider is True)
    ):
        all_divider_pk = getattr(user, DIVIDER_MODELs_LOWER).values_list(
            'pk', flat=True
        )
        divider_field_pk = f"{DIVIDER_MODEL_LOWER}_id__in"
        divided_qs = instances_qs.filter(
            **{divider_field_pk: all_divider_pk}
        ).values_list('pk', flat=True)
        write_instances_uids = write_instances_uids.union(divided_qs)

    read_instances_uids = write_instances_uids
    if include_view_groups is True:
        read_instances_uids = read_instances_uids.union(can_view_groups_qs)
    if include_view_users is True:
        read_instances_uids = read_instances_uids.union(can_view_users_qs)

    write_instances_uids_set = set(
        map(str, set(filter(lambda x: x is not None, write_instances_uids)))
    )
    read_instances_uids_set = set(
        map(str, set(filter(lambda x: x is not None, read_instances_uids)))
    )
    return read_instances_uids_set, write_instances_uids_set


def add_or_remove_element_into_list(
    elt, current_list, check_list, has_changes=False
):
    """
    Adds or removes an element from a list:
      - if the element exists in the check list, and is not in the current_list
        it is added to the curent_list
      - if the element does not exist in the check_list and exists in the
        current_list, it should be removed

    example 1:
    - elt : 5
    - current_list : [1, 2, 3, 4, 5]
    - check_list : [1, 2, 3]
    => Result: the element 5 should be removed from the current_list

    example 2:
    - elt : 5
    - current_list : [1, 2, 3, 4]
    - check_list : [1, 2, 3, 5]
    => Result: the element 5 should be added to the current_list

    Arguments
    ---------
    :elt: the element to add/remove
    :current_list: the list that contains the initial elements, and will
        contain the final result
    :check_list:: the list used to check whether the element should be added
        or removed from the list
    :has_changes: a boolean that is called recursively by the main method
        to describe whether the data changed

    Returns
    -------
    :has_changes: a boolean that describes whether the data has changed
    :current_list: the list of the updated elements
    """
    if elt in current_list and elt not in check_list:
        has_changes = True
        current_list.remove(elt)
    elif elt not in current_list and elt in check_list:
        has_changes = True
        current_list.append(elt)
    return has_changes, current_list


def update_instance_permission_uids(
    perm_instance, new_read_instance_uids, new_write_instance_uids, all_uids
):
    """
    Given a list of all_uids, this methods checks if the permission instance
    should be updated or not.
    If an element exists in both the all_uids and in the
    new_read/write_instance_uids, it should also exist in the read/write uids
    of the permission instance.
    On the other side, if an element exists in the all_uids but does not exist
    in the new_read/write_instance_uids, it should not exist in the read/write
    uids of the permission instance.
    The read_/write uids of the permission instance that do not appear in
    all_uids should not be removed

    Example:
    if all_uids is [1, 2, 3, 4]
    the read uids of the instance are [1, 2, 5, 6]
    and the new read uids are [1, 3, 4]
    We can see that the element 2 exists in all_uids and the read uids of the
    permission instance, but not in the new read uids, so it should be removed
    The elements 5 and 6 are in the read uid of the permission instance, but
    are neither in the new read uids, nor in all_uids, so they should not be
    removed. The final result of the red_uids are [1, 3, 4, 5, 6]
    """
    read_instance_uids = deepcopy(perm_instance.read_instance_uids)
    write_instance_uids = deepcopy(perm_instance.write_instance_uids)
    read_permission_changed = False
    write_permission_changed = False
    for uid in all_uids:
        uid_str = str(uid)
        #: Handle read instance uids
        (
            read_permission_changed,
            read_instance_uids,
        ) = add_or_remove_element_into_list(
            elt=uid_str,
            current_list=read_instance_uids,
            check_list=new_read_instance_uids,
            has_changes=read_permission_changed,
        )

        #: Handle write instance uids
        (
            write_permission_changed,
            write_instance_uids,
        ) = add_or_remove_element_into_list(
            elt=uid_str,
            current_list=write_instance_uids,
            check_list=new_write_instance_uids,
            has_changes=write_permission_changed,
        )

    if read_permission_changed or write_permission_changed:
        if read_permission_changed:
            perm_instance.read_instance_uids = read_instance_uids
        if write_permission_changed:
            perm_instance.write_instance_uids = write_instance_uids

        logger.debug(
            f'Updating permissions for {perm_instance.user.email} on '
            f'instance <{all_uids.model.__name__}>'
        )
        perm_instance.save()


def create_or_update_instance_permission_per_user(
    user,
    instances_qs,
    include_divider=True,
    include_view_groups=True,
    include_admin_groups=True,
    include_view_users=True,
    include_admin_users=True,
):
    if instances_qs.exists() is False:
        return
    if user.is_at_least_admin:
        return
    model_name = instances_qs.model.__name__
    user_groups_pks = user.concrete_groups.values_list('pk', flat=True)
    (
        read_instances_uids,
        write_instances_uids,
    ) = get_read_write_permission_users(
        user=user,
        instances_qs=instances_qs,
        user_groups_pks=user_groups_pks,
        include_divider=include_divider,
        include_view_groups=include_view_groups,
        include_admin_groups=include_admin_groups,
        include_view_users=include_view_users,
        include_admin_users=include_admin_users,
    )
    perm_instance, _ = InstancePermission.objects.get_or_create(
        user=user, model_name=model_name
    )

    update_instance_permission_uids(
        perm_instance=perm_instance,
        new_read_instance_uids=read_instances_uids,
        new_write_instance_uids=write_instances_uids,
        all_uids=instances_qs.values_list('pk', flat=True),
    )


def update_created_by_permissions(instance, user):
    #: The creator of the instance has the read and write access
    #: if the minimal levels on the datamodel allow it
    model = instance._meta.model
    model_name = model.__name__
    has_read_permission = check_minimum_level('GET', user, model)
    has_write_permission = check_minimum_level('PATCH', user, model)
    defaults = {}
    if has_read_permission is True:
        defaults['read_instance_uids'] = [str(instance.pk)]
    if has_write_permission is True:
        defaults['write_instance_uids'] = [str(instance.pk)]
    if not defaults:
        return
    permission_instance, created = InstancePermission.objects.get_or_create(
        user=user, model_name=model_name, defaults=defaults
    )
    if created is False:
        for field_name, field_value in defaults.items():
            getattr(permission_instance, field_name).extend(field_value)
        permission_instance.save()
