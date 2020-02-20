# coding: utf-8
from django.apps import apps
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

from concrete_datastore.api.v1.views import (
    remove_instances_user_tracked_fields,
)
from concrete_datastore.concrete.models import (
    DIVIDER_MODEL,
    ConcretePermission,
)
from concrete_datastore.concrete.meta import meta_models


class Command(BaseCommand):
    help = 'Init Applications (create groups, permissions, etc.)'

    def handle(self, *args, **options):
        UserModel = get_user_model()
        for user_blocked in UserModel.objects.filter(is_active=False):
            divider_manager = getattr(
                user_blocked, '{}s'.format(DIVIDER_MODEL.lower())
            )
            user_dividers = divider_manager.values_list('uid', flat=True)
            remove_instances_user_tracked_fields(user_blocked, user_dividers)
            divider_manager.clear()
            user_blocked.concrete_groups.clear()

        all_dividers = apps.get_model(
            "concrete.{}".format(DIVIDER_MODEL)
        ).objects.all()
        for user_active in UserModel.objects.filter(is_active=True):
            divider_manager = getattr(
                user_active, '{}s'.format(DIVIDER_MODEL.lower())
            )
            user_dividers = divider_manager.all()
            dividers_to_remove = all_dividers.difference(user_dividers)
            remove_instances_user_tracked_fields(
                user_active, dividers_to_remove.values_list('uid', flat=True)
            )

        for meta_model in meta_models:
            if meta_model.get_model_name() in [
                "EntityDividerModel",
                "UndividedModel",
            ]:
                continue
            model_name = meta_model.get_model_name()
            # pylint: disable=no-member
            ConcretePermission.objects.get_or_create(model_name=model_name)
