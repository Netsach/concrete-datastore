# coding: utf-8
import io
import os
from django.test import TestCase
from concrete_datastore.concrete.models import Project, DeletedModel
from django.test import override_settings


@override_settings(DEBUG=True)
class FileFieldDeleteTestCase(TestCase):
    def test_file_removed_existing_file(self):
        project_picture = io.BytesIO()
        project_picture.write(b'fake image data')
        project = Project.objects.create(name='project test')
        project.picture.save('picture.jpg', project_picture)
        project_picture_path = project.picture.path
        self.assertTrue(os.path.exists(project_picture_path))
        self.assertEqual(DeletedModel.objects.count(), 0)
        project.delete()
        self.assertFalse(os.path.exists(project_picture_path))
        self.assertEqual(DeletedModel.objects.count(), 1)

    def test_file_removed_non_existing_file(self):
        project = Project.objects.create(name='project test')
        with self.assertRaises(Exception):
            project.picture.path
        self.assertEqual(DeletedModel.objects.count(), 0)
        project.delete()
        self.assertEqual(DeletedModel.objects.count(), 1)
