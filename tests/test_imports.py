# coding: utf-8
from django.test import TestCase
from django.test import override_settings


@override_settings(DEBUG=True)
class ImportTestSuite(TestCase):
    def test_import_tasks(self):
        from concrete_datastore.concrete.automation.tasks import (
            async_run_plugin_tasks,
        )
