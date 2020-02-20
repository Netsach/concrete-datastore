# coding: utf-8
from rest_framework.test import APITestCase
from concrete_datastore.concrete.models import User


class RegisterTestCaseEmailFilter(APITestCase):
    def setUp(self):
        pass

    def test_options_register(self):

        url = '/api/v1.1/auth/register/'
        self.assertEqual(User.objects.count(), 0)
        #: OPTIONS to get password security rules for the register url
        resp = self.client.options(url)
        self.assertIn('rules', resp.data)
        self.assertEqual(len(resp.data['rules']), 5)
        self.assertEqual(User.objects.count(), 0)

    def test_options_change_password(self):

        url = '/api/v1.1/auth/change-password/'
        self.assertEqual(User.objects.count(), 0)
        #: OPTIONS to get password security rules for the change password url
        resp = self.client.options(url)
        self.assertIn('rules', resp.data)
        self.assertEqual(len(resp.data['rules']), 5)
        self.assertEqual(User.objects.count(), 0)

    def test_options_reset_password(self):
        url = '/api/v1.1/auth/reset-password/'
        self.assertEqual(User.objects.count(), 0)
        #: OPTIONS to get password security rules for the reset password url
        resp = self.client.options(url)
        self.assertIn('rules', resp.data)
        self.assertEqual(len(resp.data['rules']), 5)
        self.assertEqual(User.objects.count(), 0)
