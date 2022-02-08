# coding: utf-8
from rest_framework.test import APITestCase
from rest_framework import status
import uuid
from concrete_datastore.concrete.models import (
    User,
    UserConfirmation,
    Project,
    ExpectedSkill,
    Category,
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

        category_1 = Category.objects.create(name="cat1")
        category_2 = Category.objects.create(name="cat2")
        self.ex_skill_1 = ExpectedSkill.objects.create(
            name="ExSkill1", category=category_1, score=20
        )
        self.ex_skill_2 = ExpectedSkill.objects.create(
            name="ExSkill2", category=category_2, score=20
        )

        self.project_1 = Project.objects.create(name="project_1")
        self.project_1.expected_skills.set((self.ex_skill_1,))

        self.project_2 = Project.objects.create(name="project_2")
        self.project_2.expected_skills.set((self.ex_skill_2,))

        self.project_3 = Project.objects.create(name="project_3")
        self.project_3.expected_skills.set((self.ex_skill_1, self.ex_skill_2))

    def test_filterable_m2m_wrong_uid(self):
        #:  test with a wrong uid format (expect a 400 BAD REQUEST)
        get_url = '/api/v1.1/project/?expected_skills__in=SOME_FAKE_UID'
        resp = self.client.get(
            get_url, HTTP_AUTHORIZATION='Token {}'.format(self.token)
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

        get_url = (
            '/api/v1.1/project/?expected_skills__in='
            f'{self.ex_skill_1.uid},SOME_FAKE_UID'
        )
        resp = self.client.get(
            get_url, HTTP_AUTHORIZATION='Token {}'.format(self.token)
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_filterable_m2m(self):
        #:  Expected Skill 1 ==> Project 1 & 3
        get_url = (
            f'/api/v1.1/project/?expected_skills__in={self.ex_skill_1.uid}'
        )
        resp = self.client.get(
            get_url, HTTP_AUTHORIZATION='Token {}'.format(self.token)
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        self.assertIn('objects_count', resp.data)
        self.assertIn('results', resp.data)

        result_uids = set(result['uid'] for result in resp.data['results'])
        self.assertEqual(resp.data['objects_count'], 2)
        self.assertSetEqual(
            result_uids,
            set([str(self.project_1.uid), str(self.project_3.uid)]),
        )

        exclude_url = (
            f'/api/v1.1/project/?expected_skills__in!={self.ex_skill_1.uid}'
        )
        resp = self.client.get(
            exclude_url, HTTP_AUTHORIZATION='Token {}'.format(self.token)
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        self.assertIn('objects_count', resp.data)
        self.assertIn('results', resp.data)

        result_uids = set(result['uid'] for result in resp.data['results'])
        self.assertEqual(resp.data['objects_count'], 1)
        self.assertEqual(
            resp.data['results'][0]['uid'], str(self.project_2.uid)
        )

        #:  Expected Skills 1 & 2 ==> Project 1, 2 & 3
        get_url = (
            '/api/v1.1/project/?expected_skills__in='
            f'{self.ex_skill_1.uid},{self.ex_skill_2.uid}'
        )
        resp = self.client.get(
            get_url, HTTP_AUTHORIZATION='Token {}'.format(self.token)
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        self.assertIn('objects_count', resp.data)
        self.assertIn('results', resp.data)

        result_uids = set(result['uid'] for result in resp.data['results'])
        self.assertEqual(resp.data['objects_count'], 3)
        self.assertSetEqual(
            result_uids,
            set(
                [
                    str(self.project_1.uid),
                    str(self.project_2.uid),
                    str(self.project_3.uid),
                ]
            ),
        )

    def test_filterable_m2m_not_found(self):
        #:  No results are expected
        get_url = f'/api/v1.1/project/?expected_skills__in={uuid.uuid4()}'
        resp = self.client.get(
            get_url, HTTP_AUTHORIZATION='Token {}'.format(self.token)
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        self.assertIn('objects_count', resp.data)
        self.assertIn('results', resp.data)

        self.assertEqual(resp.data['objects_count'], 0)

    def test_non_filterable_m2m(self):
        #:  members is not a filtrable field: expect a 400 BAD REQUEST
        get_url = f'/api/v1.1/project/?members__in={self.user.uid}'
        resp = self.client.get(
            get_url, HTTP_AUTHORIZATION='Token {}'.format(self.token)
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_filter_m2m_isnull(self):
        #:  All projects have at least an expected_skill
        get_url = '/api/v1.1/project/?expected_skills__isnull=true'
        resp = self.client.get(
            get_url, HTTP_AUTHORIZATION='Token {}'.format(self.token)
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn('objects_count', resp.data)
        self.assertEqual(resp.data['objects_count'], 0)

        #:  Add one project without an expected_skill
        Project.objects.create(name="project_4")

        get_url = '/api/v1.1/project/?expected_skills__isnull=true'
        resp = self.client.get(
            get_url, HTTP_AUTHORIZATION='Token {}'.format(self.token)
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn('objects_count', resp.data)

        self.assertEqual(resp.data['objects_count'], 1)
