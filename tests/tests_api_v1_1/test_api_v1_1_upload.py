# coding: utf-8
from rest_framework.test import APITestCase
from rest_framework import status
from django.conf import settings
import tempfile
import os
import shutil
from concrete_datastore.concrete.models import User, UserConfirmation, Project
from django.test import override_settings


@override_settings(DEBUG=True)
class FileUploadTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='johndoe@netsach.org', password='plop', is_active=True
        )
        # User auth
        UserConfirmation.objects.create(user=self.user, confirmed=True).save()
        url = '/api/v1.1/auth/login/'
        resp = self.client.post(
            url, {"email": "johndoe@netsach.org", "password": "plop"}
        )
        self.assertEqual(resp.status_code, 200, msg=resp.content)
        self.token = resp.data['token']
        self.files_to_remove = []
        self.created = []

    def tearDown(self):
        for file in self.files_to_remove:
            path = os.path.join(settings.MEDIA_ROOT, file)
            os.remove(path)
        for directory in self.created:
            shutil.rmtree(directory)

    def _create_test_file(self, file_name):
        directory = tempfile.mkdtemp()
        self.created.append(directory)
        path = os.path.join(directory, file_name)
        with open(path, 'w') as f:
            f.write('test123\n')
        return path

    def test_upload_file(self):

        url = '/api/v1.1/project/'
        path = self._create_test_file('test_upload.png')
        self.assertEqual(Project.objects.count(), 0)

        # assert authenticated user can upload file
        with open(path) as file_handler:
            resp = self.client.post(
                url,
                {'name': 'Project Test', 'picture': file_handler},
                HTTP_AUTHORIZATION='Token {}'.format(self.token),
                format='multipart',
            )
            # A METTRE DANS LA DOC :
            # resp = requests.post(
            #     url,
            #     {'file': file_handler},
            #     headers={
            #         'HTTP_AUTHORIZATION': 'Token {}'.format(self.token)
            #     },
            # )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        # print(resp.data)
        self.assertEqual(Project.objects.count(), 1)
        self.assertIn('created_by', resp.data)
        self.assertEqual(resp.data['created_by'], self.user.uid)

        project = Project.objects.first()
        self.assertTrue(project.picture)

        self.assertIn('url', resp.data)
        url = resp.data['url']

        file_path = resp.data['picture']
        self.files_to_remove.append(os.path.basename(file_path))

        # UPDATE File
        path = self._create_test_file('test_update.png')
        with open(path) as file_handler:
            resp = self.client.put(
                url,
                {'name': 'Project Renamed', 'picture': file_handler},
                HTTP_AUTHORIZATION='Token {}'.format(self.token),
                format='multipart',
            )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        file_path = resp.data['picture']
        self.files_to_remove.append(os.path.basename(file_path))

    def test_upload_on_error(self):
        url_upload = '/api/v1.1/project/'
        path = self._create_test_file('test_upload.png')
        # assert unauthenticated user can not upload file
        with open(path) as file_handler:
            resp = self.client.post(
                url_upload,
                {'name': 'Project Test', 'picture': file_handler},
                format='multipart',
            )
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(Project.objects.count(), 0)

        path = self._create_test_file('test_upload.txt')

        with open(path) as file_handler:
            resp = self.client.post(
                url_upload,
                {'picture': file_handler},
                HTTP_AUTHORIZATION='Token {}'.format(self.token),
                format='multipart',
            )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Project.objects.count(), 1)
        file_path = resp.data['picture']
        self.files_to_remove.append(os.path.basename(file_path))
