# coding: utf-8
import logging
from importlib import import_module
from tenacity import (
    Retrying,
    wait_fixed,
    retry_if_exception_type,
    stop_after_attempt,
)
from django.db.models import Q
from django.conf import settings
from django.contrib.auth import get_user_model

import concrete_datastore.concrete.models
from concrete_datastore.settings.celery import app
from concrete_mailer.preparers import prepare_email
from concrete_datastore.concrete.meta import meta_models
from concrete_datastore.concrete.models import (  # pylint:disable=E0611
    DIVIDER_MODEL,
    UNDIVIDED_MODEL,
    Email,
)
from concrete_datastore.api.v1.permissions import (
    update_created_by_permissions,
    create_or_update_instance_permission_per_user,
    check_instance_permissions_per_user,
    bulk_create_permission_instances,
    bulk_update_permission_instances,
)


logger = logging.getLogger(__name__)

DIVIDER_MODELs = "{}s".format(DIVIDER_MODEL)
DIVIDER_MODELs_LOWER = DIVIDER_MODELs.lower()
DIVIDER_MODEL_LOWER = DIVIDER_MODEL.lower()


@app.task
def check_all_user_permissions_async(user_pk, new_level=None):
    user = get_user_model().objects.get(pk=user_pk)
    instances_to_create, instances_to_update = check_instance_permissions_per_user(
        user=user, user_level=new_level
    )
    bulk_create_permission_instances(instances_to_create)
    bulk_update_permission_instances(instances_to_update)


@app.task
def on_update_divider_async(pk_set, instance_uid, include_divider):
    divider_model = getattr(concrete_datastore.concrete.models, DIVIDER_MODEL)
    instances_to_create = []
    instances_to_update = []
    for meta_model in meta_models:
        model_name = meta_model.get_model_name()
        if model_name in ('User', 'Group', 'Email'):
            continue
        if model_name in UNDIVIDED_MODEL:
            continue

        related_name = meta_model.get_dashed_case_class_name().replace('-', '')
        related_divider_field_name = f'divider_{related_name}s'
        for divider_pk in pk_set:
            divider_instance = divider_model.objects.get(pk=divider_pk)
            instance, should_create = create_or_update_instance_permission_per_user(
                user=get_user_model().objects.get(pk=instance_uid),
                instances_qs=getattr(
                    divider_instance, related_divider_field_name
                ).all(),
                include_divider=include_divider,
            )
            if instance is None:
                continue
            if should_create is True:
                instances_to_create.append(instance)
            else:
                instances_to_update.append(instance)
    bulk_create_permission_instances(instances_to_create)
    bulk_update_permission_instances(instances_to_update)


@app.task
def on_update_group_members_async(
    instance_model_name, instance_uid, pk_set, include_pks
):
    user_model = get_user_model()
    instance_model = getattr(
        concrete_datastore.concrete.models, instance_model_name
    )
    instance = instance_model.objects.get(pk=instance_uid)
    instances_to_create = []
    instances_to_update = []
    for meta_model in meta_models:
        model_name = meta_model.get_model_name()
        if model_name in ('User', 'Group', 'Email'):
            continue
        related_model_name = meta_model.get_slugified_name()
        if instance_model_name == 'Group':
            group_viewable_field_name = f'group_viewable_{related_model_name}s'
            viewable_qs = getattr(instance, group_viewable_field_name).all()
            group_admin_field_name = (
                f'group_administrable_{related_model_name}s'
            )
            administrable_qs = getattr(instance, group_admin_field_name).all()
            for user_pk in pk_set:
                user = user_model.objects.get(pk=user_pk)
                perm_instance, should_create = create_or_update_instance_permission_per_user(
                    user=user,
                    instances_qs=viewable_qs | administrable_qs,
                    include_admin_groups=include_pks,
                    include_view_groups=include_pks,
                )
                if perm_instance is None:
                    continue
                if should_create is True:
                    instances_to_create.append(perm_instance)
                else:
                    instances_to_update.append(perm_instance)
        else:
            #: Instance is User
            user_viewable_field_name = f'viewable_{related_model_name}s'
            viewable_qs = getattr(instance, user_viewable_field_name).all()
            user_admin_field_name = f'administrable_{related_model_name}s'
            administrable_qs = getattr(instance, user_admin_field_name).all()
            concrete_model = getattr(
                concrete_datastore.concrete.models, model_name
            )
            instances_qs = concrete_model.objects.filter(
                Q(can_admin_groups__in=pk_set) | Q(can_view_groups__in=pk_set)
            )
            perm_instance, should_create = create_or_update_instance_permission_per_user(
                user=instance,
                instances_qs=instances_qs,
                include_view_users=include_pks,
                include_admin_users=include_pks,
            )
            if perm_instance is None:
                continue
            if should_create is True:
                instances_to_create.append(perm_instance)
            else:
                instances_to_update.append(perm_instance)
    bulk_create_permission_instances(instances_to_create)
    bulk_update_permission_instances(instances_to_update)


@app.task
def on_create_instance_async(user_pk, model_name, instance_pk):
    model = getattr(concrete_datastore.concrete.models, model_name)
    instance = model.objects.get(pk=instance_pk)
    instances_to_create = []
    instances_to_update = []
    if user_pk is not None:
        user = get_user_model().objects.get(pk=user_pk)
        if user.is_at_least_admin is False:
            update_created_by_permissions(instance=instance, user=user)

    #: Assign permissions to users with scope
    if model_name in UNDIVIDED_MODEL:
        return
    instance_divider_id = getattr(instance, f"{DIVIDER_MODEL_LOWER}_id")
    if instance_divider_id is None:
        return
    for user in get_user_model().objects.filter(
        **{DIVIDER_MODELs_LOWER: instance_divider_id}
    ):
        if user.is_at_least_admin:
            continue
        instance, should_create = create_or_update_instance_permission_per_user(
            user=user, instances_qs=model.objects.filter(pk=instance_pk)
        )
        if instance is None:
            continue
        if should_create is True:
            instances_to_create.append(instance)
        else:
            instances_to_update.append(instance)
    bulk_create_permission_instances(instances_to_create)
    bulk_update_permission_instances(instances_to_update)


@app.task
def on_view_admin_groups_changed_async(
    pk_set, model_name, instance_pk, include_view_groups, include_admin_groups
):
    user_model = get_user_model()
    users_ids = (
        concrete_datastore.concrete.models.Group.objects.filter(pk__in=pk_set)
        .values_list('members', flat=True)
        .distinct()
    )
    model = getattr(concrete_datastore.concrete.models, model_name)
    instances_to_create = []
    instances_to_update = []
    for user in user_model.objects.filter(pk__in=users_ids):
        instance, should_create = create_or_update_instance_permission_per_user(
            user=user,
            instances_qs=model.objects.filter(pk=instance_pk),
            include_view_groups=include_view_groups,
            include_admin_groups=include_admin_groups,
        )
        if instance is None:
            continue
        if should_create is True:
            instances_to_create.append(instance)
        else:
            instances_to_update.append(instance)
    bulk_create_permission_instances(instances_to_create)
    bulk_update_permission_instances(instances_to_update)


@app.task
def on_view_admin_users_changed_async(
    pk_set, model_name, instance_pk, include_admin_users, include_view_users
):
    user_model = get_user_model()
    model = getattr(concrete_datastore.concrete.models, model_name)
    instances_to_create = []
    instances_to_update = []
    for user in user_model.objects.filter(pk__in=pk_set):
        instance, should_create = create_or_update_instance_permission_per_user(
            user=user,
            instances_qs=model.objects.filter(pk=instance_pk),
            include_admin_users=include_admin_users,
            include_view_users=include_view_users,
        )
        if instance is None:
            continue
        if should_create is True:
            instances_to_create.append(instance)
        else:
            instances_to_update.append(instance)
    bulk_create_permission_instances(instances_to_create)
    bulk_update_permission_instances(instances_to_update)


@app.task
def async_run_plugin_tasks():
    if isinstance(settings.PLUGINS_TASKS_FUNC, dict) is False:
        return
    for path_task, queue in settings.PLUGINS_TASKS_FUNC.items():
        module_name, func_name = path_task.rsplit('.', 1)
        module = import_module(module_name)
        function = getattr(module, func_name)
        function.apply_async(queue=queue)


@app.task
def send_async_mails(email_pk):
    email = Email.objects.get(pk=email_pk)
    perform_send_email(instance=email, is_async=True)


def save_instance_if_async(instance, is_async):
    #: If this method is callled from an async process, save the instance
    #: Otherwise, this method is called directly from the pre_save
    #: signal and the instance will be saved after the signal
    if is_async is True:
        instance.save()


def perform_send_email(instance, enable_retrying=True, is_async=False):
    def _perform_send_email():
        #: Refresh instance
        if not instance.subject or not instance.body or not instance.receiver:
            instance.resource_status = 'send-error'
            instance.resource_message = 'Some fields are empty'
            save_instance_if_async(instance=instance, is_async=is_async)
            return

        if instance.created_by is None:
            instance.resource_status = 'send-error'
            instance.resource_message = 'No sender available'
            save_instance_if_async(instance=instance, is_async=is_async)
            return
        use_tls = not getattr(settings, 'DEBUG', False)
        email = prepare_email(
            context={"sender_name": settings.EMAIL_SENDER_NAME},
            css=settings.EMAIL_CSS,
            html=instance.body,
            title=instance.subject,
            sender=settings.SERVER_EMAIL,
            recipients=[instance.receiver.email],
            use_tls=use_tls,
            email_host=settings.EMAIL_HOST,
            email_port=settings.EMAIL_PORT,
            email_host_user=settings.EMAIL_HOST_USER,
            email_host_password=settings.EMAIL_HOST_PASSWORD,
        )
        email.send()

        instance.resource_status = 'sent'
        instance.resource_message = 'Mail successfuly sent'
        save_instance_if_async(instance=instance, is_async=is_async)

    try:
        if enable_retrying is False:
            _perform_send_email()
        else:
            send_email_retryer = Retrying(
                retry=retry_if_exception_type(),
                wait=wait_fixed(settings.RETRYING_DELAY_SECONDS),
                stop=stop_after_attempt(settings.MAX_RETRIES),
            )
            send_email_retryer(_perform_send_email)
    except Exception as e:
        logger.info(
            f'ERROR : Unable to send email {instance.pk} '
            f'to {instance.receiver.email}, {str(e)}'
        )
        instance.resource_status = 'send-error'
        instance.resource_message = 'Unable to send email'
        save_instance_if_async(instance=instance, is_async=is_async)
