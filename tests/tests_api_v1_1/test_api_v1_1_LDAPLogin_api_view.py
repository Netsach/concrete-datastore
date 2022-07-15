# coding: utf-8
from django.test import TestCase
from concrete_datastore.concrete.models import User, UserConfirmation


class TestLdapLoginApiView(TestCase):
    def setUp(self):
        self.url = "/api/v1.1/auth/ldap/login"
        self.user = User.objects.create_user(
            'johndoe@netsach.org'
            # 'John',
            # 'Doe',
        )
        self.user.set_password('plop')
        self.user.save()
        self.confirmation = UserConfirmation.objects.create(user=self.user)
        self.confirmation.confirmed = True
        self.confirmation.save()

    def test_post_ldap_good_login(self):
        data = {
            "username": "johndoe@netsach.org",
            "password": "plop",
        }
        response = self.client.post(
            self.url,
            data,
        )
        self.assertEqual(response.status_code, 200, msg=response.content)

    def test_post_ldap_user_does_not_exist(self):
        data = {
            "username": "test_not_exist@netsach.org",
            "password": "bad_password",
        }
        response = self.client.post(
            self.url,
            data,
        )
        self.assertEqual(response.status_code, 401)

    def test_post_ldap_login_bad_data(self):
        data = {
            "invalid_param": "data_invalid",
            "password": "plop",
        }
        response = self.client.post(
            self.url,
            data,
        )
        self.assertEqual(response.status_code, 400)
