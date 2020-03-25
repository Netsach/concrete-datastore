# coding: utf-8
import os
import glob
import hashlib
import logging
from importlib import import_module
from collections import defaultdict

from django.utils.translation import ugettext_lazy as _
from django.apps import AppConfig
from django.conf import settings
from django.apps import apps


logger_archive_users = logging.getLogger('archive-concrete-users')
logger_update_pendulum = logging.getLogger('update-pendulum-v2')


def email_to_username(email):  # nosec
    return hashlib.md5(email.lower().encode('utf-8')).hexdigest()[:30]


def archive_legacy(user, email_list):
    base_email = "ghost{}@netsach.org"
    incrementation = 0
    while base_email.format(incrementation or '') in email_list:
        incrementation += 1
    new_email = base_email.format(incrementation or '')
    previous_email = user.email
    user.email = new_email
    user.save()
    logger_archive_users.info(
        f'User {user.uid}: changed email form '
        f'{previous_email} to {new_email}'
    )
    email_list.append(new_email)


def purge_users_with_wrong_usernames(user_model):
    correspondances = defaultdict(set)
    for u in user_model.objects.all():
        correspondances[u.email].add(u)

    multi_correspondances = {
        email: users_list
        for email, users_list in correspondances.items()
        if len(users_list) > 1
    }

    email_list = list(correspondances.keys())
    if len(email_list) == 0:
        logger_archive_users.debug('No migration required for legacy users')
        return
    for email, users in multi_correspondances.items():
        for user in users:
            if user.username != email_to_username(email):
                archive_legacy(user=user, email_list=email_list)


def alter_migration_content(file):
    file_changed = False
    with open(file, 'rb') as fd:
        content = fd.read()
        if b'import pendulum.pendulum' in content:
            file_changed = True
            content = content.replace(
                b'pendulum.pendulum.Pendulum', b'pendulum'
            ).replace(b'import pendulum.pendulum', b'import pendulum')
    if file_changed is True:
        logger_update_pendulum.debug(
            f'Updating pendulum import for migration file {file}'
        )
        with open(file, 'wb') as fd:
            fd.write(content)


def get_migration_files():
    migrations_dir = set()
    for migration_module in settings.MIGRATION_MODULES.values():
        module = import_module(migration_module)
        migrations_dir.add(os.path.dirname(module.__file__))

    migration_files = []
    for migration_dir in migrations_dir:
        migration_files.extend([f for f in glob.glob(migration_dir + "/*.py")])

    return migration_files


def update_pendulum_for_migrations():
    migration_files = get_migration_files()
    for migration_file in migration_files:
        alter_migration_content(file=migration_file)


class Config(AppConfig):
    name = 'concrete_datastore.concrete'
    label = 'concrete'
    verbose_name = _('NS concrete')

    def ready(self):
        logger_update_pendulum.debug(
            'Checking for pendulum updates in migrations'
        )
        update_pendulum_for_migrations()
        user_model = apps.get_model('concrete', 'User')
        try:
            purge_users_with_wrong_usernames(user_model=user_model)
        except Exception:
            #: legacy process when upgrading from concrete-server
            logger_archive_users.debug(
                'App Concrete not yet loaded, skipping User checks ...'
            )

        from .automation import signal_processor

        if signal_processor is None:
            raise ValueError("Missing module 'signal_processor' in automation")
