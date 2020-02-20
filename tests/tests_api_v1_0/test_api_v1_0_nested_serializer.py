# coding: utf-8
from rest_framework.test import APITestCase
from rest_framework import status
from concrete_datastore.concrete.models import (
    User,
    UserConfirmation,
    Category,
    Skill,
    Project,
    ExpectedSkill,
)
import json
import os
from django.conf import settings
from django.test import override_settings


@override_settings(DEBUG=True)
class NestedSerializerTestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            'johndoe@netsach.org'
            # 'John',
            # 'Doe',
        )
        self.user.set_password('plop')
        self.user.admin = True
        self.user.save()
        UserConfirmation.objects.create(user=self.user, confirmed=True).save()
        url = '/api/v1/auth/login/'
        resp = self.client.post(
            url,
            {
                # "username": 'johndoe@netsach.org',
                "email": "johndoe@netsach.org",
                "password": "plop",
            },
        )
        self.token = resp.data['token']
        self.root = '{}://{}:{}/'.format(
            settings.SCHEME, settings.HOSTNAME, settings.PORT
        )

    def test_nested_fk(self):
        url_skills = '/api/v1/skill/'
        url_categories = '/api/v1/category/'

        resp = self.client.post(
            url_categories,
            {"name": "Category1"},
            HTTP_AUTHORIZATION='Token {}'.format(self.token),
        )
        self.assertEqual(
            resp.status_code, status.HTTP_201_CREATED, msg=resp.content
        )
        resp = self.client.post(
            url_categories,
            {"name": "Category0"},
            HTTP_AUTHORIZATION='Token {}'.format(self.token),
        )
        self.assertEqual(
            resp.status_code, status.HTTP_201_CREATED, msg=resp.content
        )

        category_pk = resp.data["uid"]
        self.assertEqual(Category.objects.count(), 2)
        category = Category.objects.get(name="Category0")
        self.assertEqual(str(category.uid), category_pk)

        resp = self.client.post(
            url_skills,
            json.dumps(
                {
                    "name": "Skill1",
                    "description": "azerty",
                    "score": 10,
                    "category_uid": None,
                    "user_uid": None,
                }
            ),
            content_type="application/json",
            HTTP_AUTHORIZATION='Token {}'.format(self.token),
        )
        self.assertEqual(
            resp.status_code, status.HTTP_201_CREATED, msg=resp.content
        )
        self.assertEqual(Skill.objects.count(), 1)
        skill_created = Skill.objects.first()

        self.assertEqual(skill_created.name, "Skill1")
        self.assertEqual(skill_created.description, "azerty")
        self.assertEqual(skill_created.score, 10)
        self.assertIsNone(skill_created.category)
        self.assertIsNone(skill_created.user)

        self.assertIn("url", resp.data)
        url = resp.data['url']
        # print(url)

        resp = self.client.patch(
            url,
            json.dumps({"category_uid": str(category.pk)}),
            content_type="application/json",
            HTTP_AUTHORIZATION='Token {}'.format(self.token),
        )
        self.assertEqual(
            resp.status_code, status.HTTP_200_OK, msg=resp.content
        )

        self.assertEqual(Skill.objects.count(), 1)
        skill_created = Skill.objects.first()

        self.assertEqual(skill_created.name, "Skill1")
        self.assertEqual(skill_created.description, "azerty")
        self.assertEqual(skill_created.score, 10)
        self.assertIsNotNone(skill_created.category)
        self.assertEqual(skill_created.category.pk, category.pk)
        self.assertIsNone(skill_created.user)

        resp = self.client.get(
            url, HTTP_AUTHORIZATION='Token {}'.format(self.token)
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn("category", resp.data)
        # print(resp.data)
        self.assertEqual(resp.data["category"]["name"], "Category0")
        self.assertIn("category_uid", resp.data)

        # patch du champs nested,
        resp = self.client.patch(
            url,
            json.dumps({"category": {"name": "BLABLA"}}),
            content_type="application/json",
            HTTP_AUTHORIZATION='Token {}'.format(self.token),
        )
        # print(resp.data)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        # On verrifie que le patch n'a rien modifié
        resp = self.client.get(
            url, {}, HTTP_AUTHORIZATION='Token {}'.format(self.token)
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn("category", resp.data)
        self.assertEqual(resp.data["category"]["name"], "Category0")
        self.assertIn("category_uid", resp.data)

        # patch de category_uid
        resp = self.client.patch(
            url,
            json.dumps({"category_uid": None}),
            content_type="application/json",
            HTTP_AUTHORIZATION='Token {}'.format(self.token),
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        # Vérification du nested
        resp = self.client.get(
            url, {}, HTTP_AUTHORIZATION='Token {}'.format(self.token)
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn("category", resp.data)
        self.assertEqual(resp.data["category_uid"], None)
        self.assertEqual(resp.data["category"], None)

    def test_good_url_api(self):
        url_skills = '/api/v1/skill/'
        url_categories = '/api/v1/category/'

        resp = self.client.post(
            url_categories,
            {"name": "Category1"},
            HTTP_AUTHORIZATION='Token {}'.format(self.token),
        )
        self.assertEqual(
            resp.status_code, status.HTTP_201_CREATED, msg=resp.content
        )
        resp = self.client.post(
            url_categories,
            {"name": "Category0"},
            HTTP_AUTHORIZATION='Token {}'.format(self.token),
        )
        self.assertEqual(
            resp.status_code, status.HTTP_201_CREATED, msg=resp.content
        )

        category_pk = resp.data["uid"]
        self.assertEqual(Category.objects.count(), 2)
        category = Category.objects.get(name="Category0")
        self.assertEqual(str(category.uid), category_pk)

        resp = self.client.post(
            url_skills,
            json.dumps(
                {
                    "name": "Skill1",
                    "description": "azerty",
                    "score": 10,
                    "category_uid": None,
                    "user_uid": None,
                }
            ),
            content_type="application/json",
            HTTP_AUTHORIZATION='Token {}'.format(self.token),
        )
        self.assertEqual(
            resp.status_code, status.HTTP_201_CREATED, msg=resp.content
        )
        self.assertEqual(Skill.objects.count(), 1)
        skill_created = Skill.objects.first()

        self.assertEqual(skill_created.name, "Skill1")
        self.assertEqual(skill_created.description, "azerty")
        self.assertEqual(skill_created.score, 10)
        self.assertIsNone(skill_created.category)
        self.assertIsNone(skill_created.user)

        self.assertIn("url", resp.data)
        url = resp.data['url']
        # print(url)

        resp = self.client.patch(
            url,
            json.dumps({"category_uid": str(category.pk)}),
            content_type="application/json",
            HTTP_AUTHORIZATION='Token {}'.format(self.token),
        )
        self.assertEqual(
            resp.status_code, status.HTTP_200_OK, msg=resp.content
        )

        self.assertEqual(Skill.objects.count(), 1)
        skill_created = Skill.objects.first()

        self.assertEqual(skill_created.name, "Skill1")
        self.assertEqual(skill_created.description, "azerty")
        self.assertEqual(skill_created.score, 10)
        self.assertIsNotNone(skill_created.category)
        self.assertEqual(skill_created.category.pk, category.pk)
        self.assertIsNone(skill_created.user)

        resp = self.client.get(
            url, HTTP_AUTHORIZATION='Token {}'.format(self.token)
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn("category", resp.data)
        # print(resp.data)
        self.assertEqual(resp.data["category"]["name"], "Category0")
        self.assertIn("category_uid", resp.data)
        start_url = os.path.join(self.root, 'api/v1/category/')
        self.assertTrue(resp.data["category"]["url"].startswith(start_url))

    def test_nested_manytomany_fk(self):
        url_e_skills = '/api/v1/expected-skill/'
        url_categories = '/api/v1/category/'
        url_projects = '/api/v1/project/'

        resp = self.client.post(
            url_categories,
            {"name": "Category1"},
            HTTP_AUTHORIZATION='Token {}'.format(self.token),
        )
        self.assertEqual(
            resp.status_code, status.HTTP_201_CREATED, msg=resp.content
        )
        category1_pk = resp.data["uid"]

        resp = self.client.post(
            url_categories,
            {"name": "Category2"},
            HTTP_AUTHORIZATION='Token {}'.format(self.token),
        )
        self.assertEqual(
            resp.status_code, status.HTTP_201_CREATED, msg=resp.content
        )
        category2_pk = resp.data["uid"]

        self.assertEqual(Category.objects.count(), 2)
        category1 = Category.objects.get(name="Category1")
        self.assertEqual(str(category1.uid), category1_pk)
        category2 = Category.objects.get(name="Category2")
        self.assertEqual(str(category2.uid), category2_pk)

        resp = self.client.post(
            url_e_skills,
            json.dumps(
                {
                    "name": "ESkill1",
                    "description": "azerty",
                    "score": 10,
                    "category_uid": str(category1.pk),
                    "user_uid": None,
                }
            ),
            content_type="application/json",
            HTTP_AUTHORIZATION='Token {}'.format(self.token),
        )
        self.assertEqual(
            resp.status_code, status.HTTP_201_CREATED, msg=resp.content
        )

        resp = self.client.post(
            url_e_skills,
            json.dumps(
                {
                    "name": "ESkill2",
                    "description": "azerty",
                    "score": 20,
                    "category_uid": str(category2.pk),
                    "user_uid": None,
                }
            ),
            content_type="application/json",
            HTTP_AUTHORIZATION='Token {}'.format(self.token),
        )
        self.assertEqual(
            resp.status_code, status.HTTP_201_CREATED, msg=resp.content
        )

        self.assertEqual(ExpectedSkill.objects.count(), 2)
        e_skill1 = ExpectedSkill.objects.get(name="ESkill1")
        e_skill2 = ExpectedSkill.objects.get(name="ESkill2")

        self.assertEqual(e_skill1.name, "ESkill1")
        self.assertEqual(e_skill1.description, "azerty")
        self.assertEqual(e_skill1.score, 10)
        self.assertEqual(e_skill1.category.pk, category1.pk)

        self.assertEqual(e_skill2.name, "ESkill2")
        self.assertEqual(e_skill2.description, "azerty")
        self.assertEqual(e_skill2.score, 20)
        self.assertEqual(e_skill2.category.pk, category2.pk)

        resp = self.client.post(
            url_projects,
            json.dumps(
                {
                    "name": "Projet1",
                    "description": "projet test",
                    "members_uid": [str(self.user.pk)],
                    "expected_skills_uid": [str(e_skill2.pk)],
                }
            ),
            content_type="application/json",
            HTTP_AUTHORIZATION='Token {}'.format(self.token),
        )
        self.assertEqual(
            resp.status_code, status.HTTP_201_CREATED, msg=resp.content
        )
        url = resp.data['url']
        self.assertEqual(Project.objects.count(), 1)
        project_created = Project.objects.first()

        self.assertEqual(project_created.name, "Projet1")
        self.assertEqual(project_created.description, "projet test")
        self.assertNotEqual(project_created.members.count(), 0)
        self.assertNotEqual(project_created.expected_skills.count(), 0)

        resp = self.client.get(
            url, HTTP_AUTHORIZATION='Token {}'.format(self.token)
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertNotEqual(resp.data["members_uid"], [])
        self.assertNotEqual(resp.data["expected_skills_uid"], [])
        self.assertEqual(len(resp.data["expected_skills_uid"]), 1)
        self.assertEqual(resp.data["expected_skills_uid"], [e_skill2.pk])

        resp = self.client.patch(
            url,
            json.dumps({"expected_skills_uid": [str(e_skill1.pk)]}),
            content_type="application/json",
            HTTP_AUTHORIZATION='Token {}'.format(self.token),
        )
        self.assertEqual(
            resp.status_code, status.HTTP_200_OK, msg=resp.content
        )
        self.assertEqual(len(resp.data["expected_skills_uid"]), 1)

        resp = self.client.patch(
            url,
            json.dumps(
                {"expected_skills": [str(e_skill1.pk), str(e_skill2.pk)]}
            ),
            content_type="application/json",
            HTTP_AUTHORIZATION='Token {}'.format(self.token),
        )
        self.assertEqual(
            resp.status_code, status.HTTP_200_OK, msg=resp.content
        )

        # on a patché un champs read_only, on doit vérifier que ça n'a pas été
        # modifié par la requête.
        self.assertEqual(len(resp.data["expected_skills_uid"]), 1)
