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
from django.test import override_settings


@override_settings(DEBUG=True)
class ReverseRelationTestCase(APITestCase):
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
        url = '/api/v1.1/auth/login/'
        resp = self.client.post(
            url,
            {
                "email": "johndoe@netsach.org",
                "password": "plop",
            },
        )
        self.token = resp.data['token']

    def test_reverse_relation_fk(self):
        url_skills = '/api/v1.1/skill/'
        url_categories = '/api/v1.1/category/'

        resp = self.client.post(
            url_categories,
            {"name": "Category0"},
            HTTP_AUTHORIZATION='Token {}'.format(self.token),
        )
        self.assertEqual(
            resp.status_code, status.HTTP_201_CREATED, msg=resp.content
        )

        category_pk = resp.data["uid"]
        category_url = resp.data["url"]
        self.assertEqual(Category.objects.count(), 1)
        category = Category.objects.get(name="Category0")
        self.assertEqual(str(category.uid), category_pk)

        resp = self.client.post(
            url_skills,
            json.dumps(
                {
                    "name": "Skill1",
                    "description": "azerty",
                    "score": 10,
                    "category_uid": category_pk,
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
        self.assertIsNotNone(skill_created.category)
        self.assertIsNone(skill_created.user)

        self.assertIn("category_uid", resp.data)
        self.assertEqual(str(resp.data['category_uid']), category_pk)

        resp = self.client.get(
            category_url, HTTP_AUTHORIZATION='Token {}'.format(self.token)
        )
        # Check reverse relation
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn("skills", resp.data)
        # print(resp.data)
        self.assertEqual(resp.data["skills"], [skill_created.uid])

        # Add another skill with same category
        resp = self.client.post(
            url_skills,
            json.dumps(
                {
                    "name": "Skill2",
                    "description": "qwerty",
                    "score": 20,
                    "category_uid": category_pk,
                    "user_uid": None,
                }
            ),
            content_type="application/json",
            HTTP_AUTHORIZATION='Token {}'.format(self.token),
        )
        self.assertEqual(
            resp.status_code, status.HTTP_201_CREATED, msg=resp.content
        )
        self.assertEqual(Skill.objects.count(), 2)
        skill2_created = Skill.objects.first()

        self.assertEqual(skill2_created.name, "Skill2")
        self.assertEqual(skill2_created.description, "qwerty")
        self.assertEqual(skill2_created.score, 20)
        self.assertIsNotNone(skill2_created.category)
        self.assertIsNone(skill2_created.user)

        self.assertIn("category_uid", resp.data)
        self.assertEqual(str(resp.data['category_uid']), category_pk)

        resp = self.client.get(
            category_url, HTTP_AUTHORIZATION='Token {}'.format(self.token)
        )
        # Check reverse relation
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn("skills", resp.data)
        # print(resp.data)
        self.assertEqual(
            set(resp.data["skills"]),
            set([skill2_created.uid, skill_created.uid]),
        )

    def test_reverse_relation_m2m(self):
        url_e_skills = '/api/v1.1/expected-skill/'
        url_projects = '/api/v1.1/project/'
        url_categories = '/api/v1.1/category/'

        resp = self.client.post(
            url_categories,
            {"name": "Category1"},
            HTTP_AUTHORIZATION='Token {}'.format(self.token),
        )
        self.assertEqual(
            resp.status_code, status.HTTP_201_CREATED, msg=resp.content
        )
        category1_pk = resp.data["uid"]
        self.assertEqual(Category.objects.count(), 1)
        category1 = Category.objects.get(name="Category1")
        self.assertEqual(str(category1.uid), category1_pk)

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
        e_skill1_url = resp.data['url']

        resp = self.client.post(
            url_e_skills,
            json.dumps(
                {
                    "name": "ESkill2",
                    "description": "azerty",
                    "score": 20,
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
        e_skill2_url = resp.data['url']

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
        self.assertEqual(e_skill2.category.pk, category1.pk)

        resp = self.client.post(
            url_projects,
            json.dumps(
                {
                    "name": "Projet1",
                    "description": "projet test",
                    "members_uid": [str(self.user.pk)],
                    "expected_skills_uid": [
                        str(e_skill1.pk),
                        str(e_skill2.pk),
                    ],
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
        self.assertEqual(len(resp.data["expected_skills_uid"]), 2)
        self.assertEqual(
            set(resp.data["expected_skills_uid"]),
            set([e_skill2.pk, e_skill1.pk]),
        )

        resp = self.client.get(
            e_skill1_url, HTTP_AUTHORIZATION='Token {}'.format(self.token)
        )
        self.assertEqual(
            resp.status_code, status.HTTP_200_OK, msg=resp.content
        )
        self.assertEqual(resp.data["projects"], [project_created.pk])

        resp = self.client.get(
            e_skill2_url, HTTP_AUTHORIZATION='Token {}'.format(self.token)
        )
        self.assertEqual(
            resp.status_code, status.HTTP_200_OK, msg=resp.content
        )
        self.assertEqual(resp.data["projects"], [project_created.pk])
