# coding: utf-8
from rest_framework.test import APITestCase
from rest_framework import status

from concrete_datastore.concrete.models import (
    User,
    UserConfirmation,
    Category,
    Skill,
)
from django.test import override_settings


@override_settings(API_MAX_PAGINATION_SIZE_NESTED=10)
class TestFiltersOrderingFK(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user('test@netsach.org')
        self.user.set_password('test')
        self.user.is_superuser = True
        self.user.save()
        UserConfirmation.objects.create(user=self.user, confirmed=True).save()
        url = '/api/v1.1/auth/login/'
        resp = self.client.post(
            url, {"email": "test@netsach.org", "password": "test"}
        )
        self.token = resp.data['token']

        self.assertEqual(Category.objects.count(), 0)
        self.assertEqual(Skill.objects.count(), 0)

        category_1 = Category.objects.create(name="cat1")
        category_2 = Category.objects.create(name="cat2")
        category_3 = Category.objects.create(name="cat3")

        skill_1_1 = Skill.objects.create(
            name="skill_a", category=category_1, score=10
        )
        skill_1_2 = Skill.objects.create(
            name="skill_b", category=category_1, score=20
        )
        skill_1_3 = Skill.objects.create(
            name="skill_c", category=category_1, score=30
        )

        skill_2_1 = Skill.objects.create(
            name="skill_e", category=category_2, score=40
        )
        skill_2_2 = Skill.objects.create(
            name="skill_f", category=category_2, score=50
        )
        skill_2_3 = Skill.objects.create(
            name="skill_g", category=category_2, score=60
        )
        skill_2_4 = Skill.objects.create(
            name="skill_h", category=category_2, score=70
        )

        skill_3_1 = Skill.objects.create(
            name="skill_i", category=category_3, score=80
        )
        skill_3_2 = Skill.objects.create(
            name="skill_j", category=category_3, score=90
        )

        self.assertEqual(Category.objects.count(), 3)
        self.assertEqual(Skill.objects.count(), 9)

    def test_filter_on_same_key(self):
        get_url = '/api/v1.1/skill/?name__in=skill_a,skill_b'

        resp = self.client.get(
            get_url, HTTP_AUTHORIZATION='Token {}'.format(self.token)
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        self.assertIn('results', resp.data)
        self.assertEqual(len(resp.data['results']), 2)

        self.assertEqual(resp.data['results'][0]['name'], 'skill_b')
        self.assertEqual(resp.data['results'][1]['name'], 'skill_a')

        self.assertEqual(resp.data['results'][0]['score'], 20)
        self.assertEqual(resp.data['results'][1]['score'], 10)

    def test_filter_on_fk(self):

        get_url = '/api/v1.1/skill/?category__name=cat1'

        resp = self.client.get(
            get_url, HTTP_AUTHORIZATION='Token {}'.format(self.token)
        )

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn('results', resp.data)
        self.assertEqual(len(resp.data['results']), 3)

        self.assertEqual(resp.data['results'][0]['score'], 30)
        self.assertEqual(resp.data['results'][1]['score'], 20)
        self.assertEqual(resp.data['results'][2]['score'], 10)

    def test_filter_on_fk_in(self):

        get_url = '/api/v1.1/skill/?category__name__in=cat1,cat2'

        resp = self.client.get(
            get_url, HTTP_AUTHORIZATION='Token {}'.format(self.token)
        )

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn('results', resp.data)
        self.assertEqual(len(resp.data['results']), 7, msg=resp.content)
