# coding: utf-8
import io
import os
from mock import patch
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
        self.assertEqual(DeletedModel.objects.count(), 0)
        project.delete()
        self.assertEqual(DeletedModel.objects.count(), 1)

    def test_file_removed_file_path_doesnot_exist(self):
        project_picture = io.BytesIO()
        project_picture.write(b'fake image data')
        project = Project.objects.create(name='project test')
        project.picture.save('picture.jpg', project_picture)
        project_picture_path = project.picture.path
        os.remove(project_picture_path)
        self.assertEqual(DeletedModel.objects.count(), 0)
        project.delete()
        self.assertEqual(DeletedModel.objects.count(), 1)

    def test_file_removed_file_delete_error(self):
        def fake_remove(*args, **kwargs):
            raise ValueError

        patch(
            'concrete_datastore.concrete.automation.signal_processor.os.remove',
            new=fake_remove,
        ).start()
        project_picture = io.BytesIO()
        project_picture.write(b'fake image data')
        project = Project.objects.create(name='project test')
        project.picture.save('picture.jpg', project_picture)
        self.assertEqual(DeletedModel.objects.count(), 0)
        project.delete()
        self.assertEqual(DeletedModel.objects.count(), 1)
        patch.stopall()
