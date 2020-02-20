# coding: utf-8
from rest_framework.test import APITestCase
from rest_framework import status
from concrete_datastore.concrete.models import (
    User,
    UserConfirmation,
    Category,
    Skill,
    Project,
)
from django.test import override_settings


@override_settings(DEBUG=True)
class CreationMinimumLevelTestCase(APITestCase):
    def setUp(self):

        # USER ADMIN
        self.user_admin = User.objects.create_user('admin@netsach.org')
        self.user_admin.set_password('plop')
        self.user_admin.admin = True
        self.user_admin.save()
        confirmation = UserConfirmation.objects.create(user=self.user_admin)
        confirmation.confirmed = True
        confirmation.save()
        url = '/api/v1.1/auth/login/'
        resp = self.client.post(
            url, {"email": "admin@netsach.org", "password": "plop"}
        )
        self.token_admin = resp.data['token']

        # USER NON ADMIN
        self.user_non_admin = User.objects.create_user('user@netsach.org')
        self.user_non_admin.set_password('plop')
        self.user_non_admin.save()
        confirmation = UserConfirmation.objects.create(
            user=self.user_non_admin
        )
        confirmation.confirmed = True
        confirmation.save()
        url = '/api/v1.1/auth/login/'
        resp = self.client.post(
            url, {"email": "user@netsach.org", "password": "plop"}
        )
        self.token_non_admin = resp.data['token']

        # USER SU
        self.user_superuser = User.objects.create_user('su@netsach.org')
        self.user_superuser.set_password('plop')
        self.user_admin.is_superuser = True
        self.user_superuser.save()
        confirmation = UserConfirmation.objects.create(
            user=self.user_superuser
        )
        confirmation.confirmed = True
        confirmation.save()
        url = '/api/v1.1/auth/login/'
        resp = self.client.post(
            url, {"email": "su@netsach.org", "password": "plop"}
        )
        self.token_superuser = resp.data['token']

        # URLS
        self.url_project = '/api/v1.1/project/'
        self.url_category = '/api/v1.1/category/'
        self.url_skill = '/api/v1.1/skill/'

        # Category TEST
        resp = self.client.post(
            self.url_category,
            {"name": "TEST"},
            HTTP_AUTHORIZATION='Token {}'.format(self.token_admin),
        )
        self.category_test = Category.objects.get(name="TEST")

    def test_non_admin_CRUD(self):

        resp = self.client.post(
            self.url_category,
            {"name": "Category1"},
            HTTP_AUTHORIZATION='Token {}'.format(self.token_non_admin),
        )
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(Category.objects.count(), 1)

        resp = self.client.post(
            self.url_project,
            {
                "name": "Proj1",
                "description": "description proj1",
                "members_uid": [],
                "expected_skills_uid": [],
            },
            HTTP_AUTHORIZATION='Token {}'.format(self.token_non_admin),
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Project.objects.count(), 1)

        resp = self.client.post(
            self.url_skill,
            {
                "name": "skill1",
                "description": "skill de test",
                "score": 10,
                "category_uid": self.category_test.uid,
                "user_uid": self.user_non_admin.uid,
            },
            HTTP_AUTHORIZATION='Token {}'.format(self.token_non_admin),
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Skill.objects.count(), 1)
        self.assertIn("category", resp.data)

        resp = self.client.patch(
            self.url_category + str(self.category_test.uid) + "/",
            {"name": "TOTO"},
            HTTP_AUTHORIZATION='Token {}'.format(self.token_non_admin),
        )
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

        resp = self.client.delete(
            self.url_category + str(self.category_test.uid) + "/",
            HTTP_AUTHORIZATION='Token {}'.format(self.token_non_admin),
        )
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(Category.objects.count(), 1)
        pass

    def test_admin_CRUD(self):

        resp = self.client.post(
            self.url_category,
            {"name": "Category1"},
            HTTP_AUTHORIZATION='Token {}'.format(self.token_admin),
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Category.objects.count(), 2)

        resp = self.client.post(
            self.url_project,
            {
                "name": "Proj1",
                "description": "description proj1",
                "members_uid": [],
                "expected_skills_uid": [],
            },
            HTTP_AUTHORIZATION='Token {}'.format(self.token_admin),
        )
        self.assertEqual(
            resp.status_code, status.HTTP_201_CREATED, msg=resp.content
        )
        self.assertEqual(Project.objects.count(), 1)

        resp = self.client.patch(
            self.url_category + str(self.category_test.uid) + "/",
            {"name": "TOTO"},
            HTTP_AUTHORIZATION='Token {}'.format(self.token_admin),
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(Category.objects.filter(name="TOTO").count(), 1)

        resp = self.client.delete(
            self.url_category + str(self.category_test.uid) + "/",
            HTTP_AUTHORIZATION='Token {}'.format(self.token_admin),
        )
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Category.objects.count(), 1)
        pass

    def test_unauth_CRUD(self):
        resp = self.client.post(self.url_category, {"name": "Category1"})
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(Category.objects.count(), 1)

        resp = self.client.post(
            self.url_project,
            {
                "name": "Proj1",
                "description": "description proj1",
                "members_uid": [],
                "expected_skills_uid": [],
            },
        )
        self.assertEqual(
            resp.status_code, status.HTTP_401_UNAUTHORIZED, msg=resp.content
        )
        self.assertEqual(Project.objects.count(), 0)
        pass
