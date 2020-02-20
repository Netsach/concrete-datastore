# coding: utf-8
from rest_framework.test import APITestCase
from django.test import override_settings
from rest_framework import status

# from uuid import uuid4
from concrete_datastore.concrete.models import User


@override_settings(DEBUG=True)
class RegisterTestCase(APITestCase):
    def setUp(self):
        pass

    @override_settings(AUTH_CONFIRM_EMAIL_ENABLE=True)
    def test_register(self):

        url = '/api/v1/auth/register/'
        self.assertEqual(User.objects.count(), 0)

        # POST informations to register a new user

        # POST correct informations
        resp = self.client.post(
            url,
            {
                "email": "johndoe@netsach.org",
                "password1": "mypassword",
                "password2": "mypassword",
            },
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.count(), 1)
        self.assertIn('token', resp.data)
        self.assertIn('email', resp.data)
        self.assertIn('first_name', resp.data)
        self.assertIn('last_name', resp.data)
        self.assertIs(
            User.objects.first().confirmations.first().link_sent, True
        )
        # POST to register with an email already taken
        resp = self.client.post(
            url,
            {
                "email": "johndoe@netsach.org",
                "password1": "mypassword3",
                "password2": "mypassword3",
            },
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_register_error_case(self):
        url = '/api/v1/auth/register/'
        # POST a non valid serializer (no field email)
        resp = self.client.post(
            url, {"password1": "mypassword", "password2": "mypasswordddd"}
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        # POST a password 2 != from password 1
        resp = self.client.post(
            url,
            {
                "email": "johndoe@netsach.org",
                "password1": "mypassword",
                "password2": "mypasswordddd",
            },
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)


@override_settings(DEBUG=True)
class RegisterTestCaseEmailLower(APITestCase):
    def setUp(self):
        pass

    def test_register_lower_case(self):

        url = '/api/v1/auth/register/'
        self.assertEqual(User.objects.count(), 0)

        # POST informations to register a new user

        # POST correct informations
        email = "JoHnDoE@netsach.org"
        email_lower = "johndoe@netsach.org"
        resp = self.client.post(
            url,
            {
                "email": email,
                "password1": "mypassword",
                "password2": "mypassword",
            },
        )
        self.assertEqual(resp.data.get('email'), email_lower)


@override_settings(API_REGISTER_EMAIL_FILTER=r'.*@netsach\.(fr|org)')
class RegisterTestCaseEmailFilter(APITestCase):
    def setUp(self):
        pass

    def test_register_email_fr(self):

        url = '/api/v1/auth/register/'
        self.assertEqual(User.objects.count(), 0)

        # POST informations to register a new user

        # POST correct informations with email ending with .fr
        resp = self.client.post(
            url,
            {
                "email": "johndoe@netsach.fr",
                "password1": "mypassword",
                "password2": "mypassword",
            },
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertIn('token', resp.data)
        self.assertIn('email', resp.data)
        self.assertIn('first_name', resp.data)
        self.assertIn('last_name', resp.data)
        self.assertEqual(User.objects.count(), 1)

    def test_register_email_com(self):

        url = '/api/v1/auth/register/'
        self.assertEqual(User.objects.count(), 0)

        # POST informations to register a new user

        # POST correct informations with email ending with .org
        resp = self.client.post(
            url,
            {
                "email": "foobar@netsach.org",
                "password1": "mypassword",
                "password2": "mypassword",
            },
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertIn('token', resp.data)
        self.assertIn('email', resp.data)
        self.assertIn('first_name', resp.data)
        self.assertIn('last_name', resp.data)
        self.assertEqual(User.objects.count(), 1)

    def test_register_error_case(self):
        url = '/api/v1/auth/register/'
        # POST an incorrect domain name
        resp = self.client.post(
            url,
            {
                "email": "johndoe@namedomain.org",
                "password1": "mypassword",
                "password2": "mypassword",
            },
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(User.objects.count(), 0)
