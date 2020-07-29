# coding: utf-8
from django.conf import settings
from django.dispatch import receiver
from django.db.models.signals import pre_delete, post_save
from django.contrib.auth import get_user_model

import concrete_datastore.concrete.models
from concrete_datastore.concrete.models import DIVIDER_MODEL
from concrete_datastore.api.v1.views import (
    remove_instances_user_tracked_fields,
)


@receiver(pre_delete)
def on_pre_delete(sender, instance, **kwargs):
    if (
        hasattr(
            concrete_datastore.concrete.models, instance.__class__.__name__
        )
        and instance.__class__.__name__
        not in settings.IGNORED_MODELS_ON_DELETE
    ):
        # pylint: disable=no-member
        concrete_datastore.concrete.models.DeletedModel.objects.create(
            model_name=instance.__class__.__name__, uid=instance.uid
        )


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
