from django.test import TestCase
from concrete_datastore.concrete.models import Project
from django.db import DataError


class UrlValidationTestCase(TestCase):
    #: URL length validator is 1024
    def test_nominal_case(self):
        url = "http://domain.ext/" + "a/" * 491
        self.assertEqual(len(url), 1000)
        # 1000 < 1024
        self.assertEqual(Project.objects.count(), 0)
        project = Project.objects.create(storage_url=url)
        self.assertEqual(Project.objects.count(), 1)
        self.assertEqual(len(project.storage_url), 1000)

    def test_validation_error(self):
        url = "http://domain.ext/" + "a/" * 991
        self.assertEqual(len(url), 2000)
        # 2000 > 1024
        self.assertEqual(Project.objects.count(), 0)
        with self.assertRaises(DataError):
            Project.objects.create(storage_url=url)
