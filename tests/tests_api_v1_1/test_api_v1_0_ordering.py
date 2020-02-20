# coding: utf-8
from rest_framework.test import APITestCase
import pendulum
from concrete_datastore.concrete.models import User, UserConfirmation, Category
from django.test import override_settings


@override_settings(DEBUG=True)
class OrderingTestCase(APITestCase):
    def setUp(self):

        self.userA = User.objects.create_user('usera@netsach.org')
        self.userA.set_password('plop')
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
            d1 = pendulum(result[i - 1].get('creation_date'))
            d2 = pendulum(result[i].get('creation_date'))
            younger = d1 > d2
            self.assertTrue(younger)
