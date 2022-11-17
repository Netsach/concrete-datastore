# coding: utf-8
from django.test import TestCase
from concrete_datastore.concrete.management.commands.get_stats_models_count import (
    get_sorted_stats,
)
from concrete_datastore.concrete.models import Project


class CreateSuperUserTests(TestCase):
    def setUp(self):
        pass

    def test_order_by_name_asc(self):
        sorted_stats = get_sorted_stats('name')
        # check that the model names are sorted
        for model_1, model_2 in zip(sorted_stats[:-1], sorted_stats[1:]):
            self.assertTrue(model_1['name'] <= model_2['name'])

    def test_order_by_name_desc(self):
        sorted_stats = get_sorted_stats('-name')
        # check that the model names are sorted
        for model_1, model_2 in zip(sorted_stats[:-1], sorted_stats[1:]):
            self.assertTrue(model_1['name'] >= model_2['name'])

    def test_order_by_count_asc(self):
        for i in range(10):
            Project.objects.create()
        sorted_stats = get_sorted_stats('count')
        # We expect that the Project model is the last model in the data
        self.assertEqual(sorted_stats[-1]['name'], 'Project')

    def test_order_by_count_desc(self):
        for i in range(10):
            Project.objects.create()
        sorted_stats = get_sorted_stats('-count')
        # We expect that the Project model is the first model in the data
        self.assertEqual(sorted_stats[0]['name'], 'Project')
