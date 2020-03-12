# coding: utf-8
import hashlib
import logging
from collections import defaultdict

from django.utils.translation import ugettext_lazy as _
from django.apps import AppConfig
from django.apps import apps


logger_archive_users = logging.getLogger('archive-concrete-users')


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


class Config(AppConfig):
    name = 'concrete_datastore.concrete'
    label = 'concrete'
    verbose_name = _('NS concrete')

    def ready(self):
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
