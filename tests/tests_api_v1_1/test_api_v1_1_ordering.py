# coding: utf-8
from rest_framework.test import APITestCase
import pendulum
from concrete_datastore.concrete.models import (
    User,
    UserConfirmation,
    Category,
    Skill,
    ExpectedSkill,
)
from django.test import override_settings


@override_settings(DEBUG=True)
class OrderingTestCase(APITestCase):
    def setUp(self):

        self.userA = User.objects.create_user('usera@netsach.org')
        self.userA.set_password('plop')
        self.userA.set_level('admin')
        self.userA.save()
        UserConfirmation.objects.create(user=self.userA, confirmed=True).save()
        url = '/api/v1.1/auth/login/'
        resp = self.client.post(
            url, {"email": "usera@netsach.org", "password": "plop"}
        )
        self.token_a = resp.data['token']

        categories = [
            {
                "name": "Category1",
                "creation_date": "2018-03-19 10:00:00Z",
                "modification_date": "2018-03-19 10:00:00Z",
            },
            {
                "name": "Category2",
                "creation_date": "2018-03-19 10:00:01Z",
                "modification_date": "2018-03-19 10:00:01Z",
            },
            {
                "name": "Category3",
                "creation_date": "2018-03-19 10:00:02Z",
                "modification_date": "2018-03-19 10:00:02Z",
            },
            {
                "name": "Category4",
                "creation_date": "2018-03-19 10:00:03Z",
                "modification_date": "2018-03-19 10:00:03Z",
            },
        ]

        for category in categories:
            c = Category.objects.create(name=category.get("name"))
            c.creation_date = category.get("creation_date")
            c.modification_date = category.get("modification_date")
            c.save()
        self.assertEqual(Category.objects.count(), 4)

    def test_ordering(self):
        url = "/api/v1.1/category/"

        rsp = self.client.get(
            url, HTTP_AUTHORIZATION='Token {}'.format(self.token_a)
        )

        result = rsp.data.get('results')

        for i in range(1, len(result)):
            d1 = pendulum.parse(result[i - 1].get('creation_date'))
            d2 = pendulum.parse(result[i].get('creation_date'))
            younger = d1 > d2
            self.assertTrue(younger)


@override_settings(DEBUG=True)
class OrderingForeignKeyTestCase(APITestCase):
    def setUp(self):

        self.userA = User.objects.create_user('usera@netsach.org')
        self.userA.set_password('plop')
        self.userA.set_level('admin')
        self.userA.save()
        UserConfirmation.objects.create(user=self.userA, confirmed=True).save()
        url = '/api/v1.1/auth/login/'
        resp = self.client.post(
            url, {"email": "usera@netsach.org", "password": "plop"}
        )
        self.token_a = resp.data['token']
        self.category1 = Category.objects.create(name="Plane")
        self.category2 = Category.objects.create(name="Culture")
        self.category3 = Category.objects.create(name="Agar")
        self.category4 = Category.objects.create(name="Student")

        # Category 3 > Category 2 > Category 1 > Category 4
        skills = [
            {
                "name": "Skill4",
                "category": self.category4,
                "creation_date": "2018-03-19 10:00:00Z",
                "modification_date": "2018-03-19 10:00:00Z",
            },
            {
                "name": "Skill2",
                "category": self.category2,
                "creation_date": "2018-03-19 10:00:01Z",
                "modification_date": "2018-03-19 10:00:01Z",
            },
            {
                "name": "Skill1",
                "category": self.category1,
                "creation_date": "2018-03-19 10:00:02Z",
                "modification_date": "2018-03-19 10:00:02Z",
            },
            {
                "name": "Skill3",
                "category": self.category3,
                "creation_date": "2018-03-19 10:00:03Z",
                "modification_date": "2018-03-19 10:00:03Z",
            },
        ]
        for skill in skills:
            s = Skill.objects.create(
                name=skill.get("name"), category=skill.get('category')
            )
            s.creation_date = skill.get("creation_date")
            s.modification_date = skill.get("modification_date")
            s.save()

        self.assertEqual(Category.objects.count(), 4)
        self.assertEqual(Skill.objects.count(), 4)

    def test_basic_ordering(self):
        url = "/api/v1.1/skill/"

        rsp = self.client.get(
            url, HTTP_AUTHORIZATION='Token {}'.format(self.token_a)
        )

        results = rsp.data.get('results')

        for i in range(1, len(results)):
            d1 = pendulum.parse(results[i - 1].get('creation_date'))
            d2 = pendulum.parse(results[i].get('creation_date'))
            younger = d1 > d2
            self.assertTrue(younger)
        self.assertEqual(
            [skill['name'] for skill in results],
            ['Skill3', 'Skill1', 'Skill2', 'Skill4'],
        )

    def test_ordering_creation_modification_date(self):
        url = "/api/v1.1/skill/"

        rsp = self.client.get(
            f'{url}?ordering=creation_date',
            HTTP_AUTHORIZATION='Token {}'.format(self.token_a),
        )

        results = rsp.data.get('results')
        self.assertEqual(
            [skill['name'] for skill in results],
            ['Skill4', 'Skill2', 'Skill1', 'Skill3'],
        )

        rsp = self.client.get(
            f'{url}?ordering=modification_date',
            HTTP_AUTHORIZATION='Token {}'.format(self.token_a),
        )

        results = rsp.data.get('results')
        self.assertEqual(
            [skill['name'] for skill in results],
            ['Skill4', 'Skill2', 'Skill1', 'Skill3'],
        )

        rsp = self.client.get(
            f'{url}?ordering=-creation_date',
            HTTP_AUTHORIZATION='Token {}'.format(self.token_a),
        )

        results = rsp.data.get('results')
        self.assertEqual(
            [skill['name'] for skill in results],
            ['Skill3', 'Skill1', 'Skill2', 'Skill4'],
        )

        rsp = self.client.get(
            f'{url}?ordering=-modification_date',
            HTTP_AUTHORIZATION='Token {}'.format(self.token_a),
        )

        results = rsp.data.get('results')
        self.assertEqual(
            [skill['name'] for skill in results],
            ['Skill3', 'Skill1', 'Skill2', 'Skill4'],
        )

    def test_ordering_against_fk_field(self):
        url = "/api/v1.1/skill/"

        rsp = self.client.get(
            f'{url}?ordering=category__name',
            HTTP_AUTHORIZATION='Token {}'.format(self.token_a),
        )

        results = rsp.data.get('results')

        self.assertEqual(
            [skill['name'] for skill in results],
            ['Skill3', 'Skill2', 'Skill1', 'Skill4'],
        )
        self.assertEqual(
            [skill['category']['name'] for skill in results],
            ['Agar', 'Culture', 'Plane', 'Student'],
        )

        rsp = self.client.get(
            f'{url}?ordering=-category__name',
            HTTP_AUTHORIZATION='Token {}'.format(self.token_a),
        )

        results = rsp.data.get('results')

        self.assertEqual(
            [skill['name'] for skill in results],
            ['Skill4', 'Skill1', 'Skill2', 'Skill3'],
        )
        self.assertEqual(
            [skill['category']['name'] for skill in results],
            ['Student', 'Plane', 'Culture', 'Agar'],
        )
