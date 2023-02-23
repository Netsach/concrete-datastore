# coding: utf-8
import logging
from django.apps import apps
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.conf import settings

import concrete_datastore
from concrete_datastore.api.v1.views import (
    remove_instances_user_tracked_fields,
)
from concrete_datastore.api.v1.permissions import (
    check_instance_permissions_per_user,
)
from concrete_datastore.concrete.models import (
    DIVIDER_MODEL,
    ConcretePermission,
    SystemVersion,
)
from concrete_datastore.concrete.meta import meta_models


logger = logging.getLogger(__name__)


def check_for_latest_version(app_name, version):
    #: The version has changed on one of these conditions
    #: - created is True
    #: - created is False and is_latest is False
    instance, created = SystemVersion.objects.get_or_create(
        app_name=app_name, version=version
    )
    version_has_changed = created
    if created is False and instance.is_latest is False:
        version_has_changed = True
        instance.is_latest = True
        instance.save()
    SystemVersion.objects.filter(app_name=app_name).exclude(
        pk=instance.pk
    ).update(is_latest=False)
    return version_has_changed


def get_datamodel_version_v1(model_definitions):
    return model_definitions['manifest']['data_modeling']['version']


data_models_version = {'1.0.0': get_datamodel_version_v1}


def get_datamodel_version():
    model_definitions = settings.META_MODEL_DEFINITIONS
    try:
        version = model_definitions['manifest']['version']
    except KeyError:
        logger.warn('Meta definition not supported')
        return None
    try:
        version_func = data_models_version[version]
        return version_func(model_definitions)
    except KeyError:
        logger.warn(f'Version {version} not supported')
        return None


def setup_versions_and_permissions():
    #: Datastore version
    concrete_version = concrete_datastore.__version__
    check_for_latest_version(
        app_name='concrete_datastore', version=concrete_version
    )

    #: Plugins versions
    for plugin_name, plugin_version in settings.INSTALLED_PLUGINS.items():
        check_for_latest_version(app_name=plugin_name, version=plugin_version)

    #: Datamodel version
    datamodel_version = get_datamodel_version()
    if datamodel_version is None:
        return
    datamodel_changed = check_for_latest_version(
        app_name='datamodel', version=datamodel_version
    )
    if datamodel_changed is True:
        for user in get_user_model().objects.filter(
            is_active=True, admin=False, is_superuser=False
        ):
            check_instance_permissions_per_user(user=user)


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

        setup_versions_and_permissions()
