# coding: utf-8
import os
from itertools import chain
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings.production')
from django.conf import settings

app = Celery('celery_app', backend='rpc://')
app.config_from_object('django.conf:settings')


def get_plugin_tasks():
    tasks = [elt['task'] for elt in settings.CELERYBEAT_SCHEDULE.values()]
    tasks.extend(settings.PLUGINS_TASKS_FUNC.keys())
    return tasks


plugin_tasks_modules = [
    plugin.rsplit('.', 1)[0]  #: module name
    for plugin in get_plugin_tasks()
    if plugin.split('.')[0] in settings.INSTALLED_PLUGINS.keys()
]

app.autodiscover_tasks(
    chain(
        ['concrete_datastore.concrete.automation.tasks'], plugin_tasks_modules
    )
)
