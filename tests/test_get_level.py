# coding: utf-8
from django.test import TestCase
from concrete_datastore.concrete.models import User


class TestLevel(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            'johndoe@netsach.org',
            # 'John',
            # 'Doe',
        )

    def test_level_simple_user(self):
        resp = self.user.get_level()
        self.assertEqual(resp, "SimpleUser")
