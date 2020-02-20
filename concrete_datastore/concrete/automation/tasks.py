# coding: utf-8
from importlib import import_module

from django.conf import settings

from concrete_datastore.settings.celery import app


@app.task
def async_run_plugin_tasks():
    if isinstance(settings.PLUGINS_TASKS_FUNC, dict) is False:
        return
    for path_task, queue in settings.PLUGINS_TASKS_FUNC.items():
        module_name, func_name = path_task.rsplit('.', 1)
        module = import_module(module_name)
        function = getattr(module, func_name)
        function.apply_async(queue=queue)
