# coding: utf-8
from rest_framework.test import APITestCase
from rest_framework import status
from concrete_datastore.concrete.models import User, UserConfirmation, Project
from django.test import override_settings


@override_settings(DEBUG=True)
class ModifyProjectTestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            'johndoe@netsach.org'
            # 'John',
            # 'Doe',
        )
        self.user.set_password('plop')
        self.user.save()
        self.confirmation = UserConfirmation.objects.create(user=self.user)
        self.confirmation.confirmed = True
        self.confirmation.save()
        url = '/api/v1.1/auth/login/'
        resp = self.client.post(
            url,
            {
                "email": "johndoe@netsach.org",
                "password": "plop",
            },
        )
        self.token = resp.data['token']

    def test_modify_Project(self):
        url_projects = '/api/v1.1/project/'
        resp = self.client.get(url_projects)
        self.assertEqual(
            resp.status_code, status.HTTP_200_OK, msg=resp.content
        )

        self.assertEqual(Project.objects.count(), 0)

        # CREATE a valid project and ensure that request is valid(202)
        resp = self.client.post(
            url_projects,
            {
                "name": "Projects2",
                # "date_creation": timezone.now(),
                "description": "description de mon projet",
                "skills": [],
                "members": [],
            },
            HTTP_AUTHORIZATION='Token {}'.format(self.token),
        )
        self.assertEqual(
            resp.status_code, status.HTTP_201_CREATED, msg=resp.content
        )
        self.assertEqual(Project.objects.count(), 1)

        self.assertIn("url", resp.data)
        self.assertIn("uid", resp.data)
