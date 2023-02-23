# coding: utf-8
import sys
import os
import logging
from django.conf import settings
from django.dispatch import receiver
from django.db.models.signals import (
    pre_delete,
    post_save,
    m2m_changed,
    pre_save,
)
from django.contrib.auth import get_user_model
import concrete_datastore.concrete.models
from concrete_datastore.concrete.models import DIVIDER_MODEL
from concrete_datastore.concrete.automation.tasks import (
    on_update_divider_async,
    on_update_group_members_async,
    on_create_instance_async,
    on_view_admin_groups_changed_async,
    on_view_admin_users_changed_async,
)
from concrete_datastore.api.v1.permissions import (
    check_instance_permissions_per_user,
)
from concrete_datastore.api.v1.views import (
    remove_instances_user_tracked_fields,
)
from concrete_datastore.concrete.meta import meta_models


logger = logging.getLogger(__name__)


DIVIDER_MODELs = "{}s".format(DIVIDER_MODEL)
DIVIDER_MODELs_LOWER = DIVIDER_MODELs.lower()
DIVIDER_MODEL_LOWER = DIVIDER_MODEL.lower()


@receiver(pre_delete)
def on_pre_delete(sender, instance, **kwargs):
    model_name = instance.__class__.__name__
    if (
        hasattr(concrete_datastore.concrete.models, model_name)
        and instance.__class__.__name__
        not in settings.IGNORED_MODELS_ON_DELETE
    ):
        # pylint: disable=no-member
        concrete_datastore.concrete.models.DeletedModel.objects.create(
            model_name=model_name, uid=instance.uid
        )

        # Remove files of a deleted instance, if this instance has a FileField
        file_fields = [
            field.name
            for field in instance._meta.fields
            if field.get_internal_type() in ['FileField', 'ImageField']
        ]
        for field_name in file_fields:
            field_value = getattr(instance, field_name)

            if not field_value:
                continue
            try:
                file_path = field_value.path
            except Exception as e:
                logger.exception(
                    f'Cannot retrieve the file path for {field_value} '
                    f'(field {field_name} of instance '
                    f'<{model_name}:{instance.uid}>). The error is {e}'
                )
                continue
            if os.path.exists(file_path) is False:
                continue
            try:
                os.remove(file_path)
            except Exception:
                logger.exception(
                    f'Error while attempting to delete file {file_path} '
                    f'(field {field_name} of instance '
                    f'<{model_name}:{instance.uid}>'
                )
                continue


@receiver(pre_save, sender=get_user_model())
def on_pre_save(sender, instance, *args, **kwargs):
    if instance.level in ('blocked', 'superuser', 'admin'):
        return
    try:
        prev_instance = get_user_model().objects.get(pk=instance.pk)
    except get_user_model().DoesNotExist:
        return
    if prev_instance.level == instance.level:
        return
    check_instance_permissions_per_user(instance)


@receiver(post_save, sender=get_user_model())
def on_post_save(sender, instance, created, **kwargs):
    if created is True and instance.level in ('simpleuser', 'manager'):
        check_instance_permissions_per_user(instance)

    if instance.level == 'blocked':
        divider_manager = getattr(
            instance, '{}s'.format(DIVIDER_MODEL.lower())
        )
        user_dividers = divider_manager.values_list('uid', flat=True)
        remove_instances_user_tracked_fields(instance, user_dividers)
        divider_manager.clear()
        instance.concrete_groups.clear()


#: If user dividers changed
@receiver(
    m2m_changed,
    sender=getattr(
        concrete_datastore.concrete.models.User, DIVIDER_MODELs_LOWER
    ).through,
)
def on_update_divider(sender, instance, action, pk_set, **kwargs):
    if action not in ('post_add', 'post_remove', 'pre_clear'):
        return

    if action == 'pre_clear':
        pk_set = getattr(instance, DIVIDER_MODELs_LOWER).values_list(
            'pk', flat=True
        )
    if pk_set is None or len(pk_set) == 0:
        #: Nothing to add/remove
        return
    on_update_divider_async.apply_async(
        kwargs={
            'include_divider': action != 'pre_clear',
            'pk_set': list(map(str, pk_set)),
            'instance_uid': str(instance.pk),
        }
    )


#: If concrete groups changed members
@receiver(
    m2m_changed,
    sender=concrete_datastore.concrete.models.Group.members.through,
)
def on_update_group_members(sender, instance, action, pk_set, **kwargs):
    #: Can be done either from the group.memebers fields, or from
    #: user.concrete_groups reverse
    if action not in ('post_add', 'post_remove', 'pre_clear'):
        return
    model_name = instance._meta.model.__name__
    if action == 'pre_clear':
        if model_name == 'Group':
            pk_set = instance.members.values_list('pk', flat=True)
        else:
            pk_set = instance.concrete_groups.values_list('pk', flat=True)

    if pk_set is None or len(pk_set) == 0:
        #: Nothing to add/remove
        return
    on_update_group_members_async.apply_async(
        kwargs={
            'include_pks': action != 'pre_clear',
            'instance_model_name': model_name,
            'instance_uid': instance.pk,
            'pk_set': list(map(str, pk_set)),
        }
    )


for meta_model in meta_models:
    model_name = meta_model.get_dashed_case_class_name().replace('-', '_')
    if model_name in ('user', 'group', 'email'):
        continue
    concrete_model = getattr(
        concrete_datastore.concrete.models, meta_model.get_model_name()
    )

    @receiver(post_save, sender=concrete_model)
    def on_create_instance(instance, created, *args, **kwargs):
        #: Assign permissions to the creator
        if created is False:
            return
        user = instance.created_by
        on_create_instance_async.apply_async(
            kwargs={
                'user_pk': None if user is None else str(user.pk),
                'model_name': instance._meta.model.__name__,
                'instance_pk': str(instance.pk),
            }
        )

    #: Signals for can_view/admin_groups
    @receiver(
        m2m_changed, sender=getattr(concrete_model, 'can_view_groups').through
    )
    @receiver(
        m2m_changed, sender=getattr(concrete_model, 'can_admin_groups').through
    )
    def on_view_admin_groups_changed(
        sender, instance, action, pk_set, *args, **kwargs
    ):
        model_name = instance._meta.model.__name__
        field_name = sender.__name__.replace(f'{model_name}_', '')
        include_admin_groups = True
        include_view_groups = True
        if action == 'pre_clear':
            pk_set = getattr(instance, field_name).values_list('pk', flat=True)
            #: If the field name is 'can_view_groups' it means that we should
            #: include the can_admin_groups and exclude the can_view_users
            #: and vice versa
            include_admin_groups = field_name == 'can_view_groups'
            include_view_groups = field_name == 'can_admin_groups'
        if pk_set is None or len(pk_set) == 0:
            #: Nothing to add/remove
            return
        if action not in ('post_add', 'post_remove', 'pre_clear'):
            return
        on_view_admin_groups_changed_async.apply_async(
            kwargs={
                'include_admin_groups': include_admin_groups,
                'include_view_groups': include_view_groups,
                'pk_set': list(map(str, pk_set)),
                'model_name': model_name,
                'instance_pk': str(instance.pk),
            }
        )

    #: Signals for can_view/admin_users
    @receiver(
        m2m_changed, sender=getattr(concrete_model, 'can_view_users').through
    )
    @receiver(
        m2m_changed, sender=getattr(concrete_model, 'can_admin_users').through
    )
    def on_view_admin_users_changed(
        sender, instance, action, pk_set, *args, **kwargs
    ):
        model_name = instance._meta.model.__name__
        field_name = sender.__name__.replace(f'{model_name}_', '')
        include_admin_users = True
        include_view_users = True
        if action == 'pre_clear':
            pk_set = getattr(instance, field_name).values_list('pk', flat=True)
            #: If the field name is 'can_view_users' it means that we should
            #: include the can_admin_users and exclude the can_view_users
            #: and vice versa
            include_admin_users = field_name == 'can_view_users'
            include_view_users = field_name == 'can_admin_users'
        if pk_set is None or len(pk_set) == 0:
            #: Nothing to add/remove
            return
        if action not in ('post_add', 'post_remove', 'pre_clear'):
            return
        model_name = instance._meta.model.__name__
        on_view_admin_users_changed_async.apply_async(
            kwargs={
                'include_admin_users': include_admin_users,
                'include_view_users': include_view_users,
                'pk_set': list(map(str, pk_set)),
                'model_name': model_name,
                'instance_pk': str(instance.pk),
            }
        )

    setattr(
        sys.modules[__name__], f'on_create_{model_name}', on_create_instance
    )
    setattr(
        sys.modules[__name__],
        f'on_view_admin_groups_changed_{model_name}',
        on_view_admin_groups_changed,
    )
    setattr(
        sys.modules[__name__],
        f'on_view_admin_users_changed_{model_name}',
        on_view_admin_users_changed,
    )
