# coding: utf-8
import os
import logging
from django.conf import settings
from django.dispatch import receiver
from django.db.models.signals import pre_delete, post_save
from django.contrib.auth import get_user_model

import concrete_datastore.concrete.models
from concrete_datastore.concrete.models import DIVIDER_MODEL
from concrete_datastore.api.v1.views import (
    remove_instances_user_tracked_fields,
)


logger = logging.getLogger(__name__)


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
            file_path = field_value.path
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


@receiver(post_save, sender=get_user_model())
def on_post_save(sender, instance, **kwargs):
    if instance.level == 'blocked':
        divider_manager = getattr(
            instance, '{}s'.format(DIVIDER_MODEL.lower())
        )
        user_dividers = divider_manager.values_list('uid', flat=True)
        remove_instances_user_tracked_fields(instance, user_dividers)
        divider_manager.clear()
        instance.concrete_groups.clear()
