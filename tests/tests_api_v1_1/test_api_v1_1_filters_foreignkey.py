# coding: utf-8
from rest_framework.test import APITestCase
from rest_framework import status

from concrete_datastore.concrete.models import (
    User,
    UserConfirmation,
    Project,
    ExpectedSkill,
    Category,
    Skill,
)


class TestFiltersFK(APITestCase):

    '''
    Skill is filterable with ForeigKeyField category
    Skill is NOT filterable with ForeigKeyField category
    '''

    def setUp(self):
        self.user = User.objects.create_user(
            'johndoe@netsach.org',
            # 'John',
            # 'Doe',
        )
        self.user.set_password('plop')
        self.user.is_superuser = True
        self.user.save()
        # User 1 auth
        UserConfirmation.objects.create(user=self.user, confirmed=True).save()
        url = '/api/v1.1/auth/login/'
        resp = self.client.post(
            url,
            {
                # "username": 'johndoe@netsach.org',
                "email": "johndoe@netsach.org",
                "password": "plop",
            },
        )
        self.token = resp.data['token']
        for i in range(20):
            Project.objects.create(name="project_name_{}".format(i))
        self.objects_count = Project.objects.count()

    def test_filterable_fk_uid(self):
        category_1 = Category.objects.create(name="cat1")
        category_2 = Category.objects.create(name="cat2")
        skill_1 = Skill.objects.create(
            name="skill1", category=category_1, score=10
        )
        skill_2 = Skill.objects.create(
            name="skill2", category=category_2, score=10
        )

        pagination = 7
        self.assertEqual(Skill.objects.count(), 2)
        get_url = (
            '/api/v1.1/skill/?c_resp_page_size={}'
            '&c_resp_nested=true&category_uid={}'.format(
                pagination, str(category_1.uid)
            )
        )
        resp = self.client.get(
            get_url, HTTP_AUTHORIZATION='Token {}'.format(self.token)
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['objects_count'], 1)
        self.assertEqual(resp.data['results'][0]['uid'], str(skill_1.uid))
        #: test exclude
        get_url = (
            '/api/v1.1/skill/?c_resp_page_size={}'
            '&c_resp_nested=true&category_uid!={}'.format(
                pagination, str(category_1.uid)
            )
        )
        resp = self.client.get(
            get_url, HTTP_AUTHORIZATION='Token {}'.format(self.token)
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['objects_count'], 1)
        self.assertEqual(resp.data['results'][0]['uid'], str(skill_2.uid))

        #:  test with a wrong uid format (expect a 400 BAD REQUEST)
        get_url = (
            '/api/v1.1/skill/?c_resp_page_size={}&c_resp_nested=true'
            '&category_uid=SOME_FAKE_UID'.format(pagination)
        )
        resp = self.client.get(
            get_url, HTTP_AUTHORIZATION='Token {}'.format(self.token)
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_filterable_fk(self):
        category_1 = Category.objects.create(name="cat1")
        category_2 = Category.objects.create(name="cat2")
        skill_1 = Skill.objects.create(
            name="skill1", category=category_1, score=10
        )
        Skill.objects.create(name="skill2", category=category_2, score=10)

        pagination = 7
        get_url = (
            '/api/v1.1/skill/?c_resp_page_size={}'
            '&c_resp_nested=true&category={}'.format(
                pagination, str(category_1.uid)
            )
        )
        resp = self.client.get(
            get_url, HTTP_AUTHORIZATION='Token {}'.format(self.token)
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(Skill.objects.count(), 2)
        self.assertEqual(resp.data['objects_count'], 1)
        self.assertEqual(resp.data['results'][0]['uid'], str(skill_1.uid))

    def test_non_filterable_fk(self):
        category_1 = Category.objects.create(name="cat1")
        category_2 = Category.objects.create(name="cat2")
        ExpectedSkill.objects.create(
            name="ExSkill1", category=category_1, score=20
        )
        ExpectedSkill.objects.create(
            name="ExSkill2", category=category_2, score=20
        )

        pagination = 7
        get_url = (
            '/api/v1.1/expected-skill/?c_resp_page_size={}'
            '&c_resp_nested=true&category={}'.format(
                pagination, str(category_1.uid)
            )
        )
        resp = self.client.get(
            get_url, HTTP_AUTHORIZATION='Token {}'.format(self.token)
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_non_filterable_fk_uid(self):
        category_1 = Category.objects.create(name="cat1")
        category_2 = Category.objects.create(name="cat2")
        ExpectedSkill.objects.create(
            name="ExSkill1", category=category_1, score=20
        )
        ExpectedSkill.objects.create(
            name="ExSkill2", category=category_2, score=20
        )

        pagination = 7
        get_url = (
            '/api/v1.1/expected-skill/?c_resp_page_size={}'
            '&c_resp_nested=true&category_uid={}'.format(
                pagination, str(category_1.uid)
            )
        )
        resp = self.client.get(
            get_url, HTTP_AUTHORIZATION='Token {}'.format(self.token)
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
