# coding: utf-8
from django.test import override_settings
from django.conf import settings

from rest_framework import status
from rest_framework.test import APITestCase

from concrete_datastore.concrete.models import (
    User,
    Email,
    PasswordChangeToken,
    UserConfirmation,
    Village,
)


@override_settings(DEBUG=True)
class RegisterWithAllowSendEmailOnRegisterTestCase(APITestCase):
    def setUp(self):
        pass

    @override_settings(ALLOW_SEND_EMAIL_ON_REGISTER=False)
    def test_register_error_without_password(self):
        #:  POST request without password should fail when
        #:  ALLOW_SEND_EMAIL_ON_REGISTER is False
        url = '/api/v1.1/auth/register/'
        self.assertEqual(User.objects.count(), 0)
        resp = self.client.post(url, {"email": "johndoe@netsach.com"})
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    @override_settings(ALLOW_SEND_EMAIL_ON_REGISTER=True)
    def test_register_with_password(self):
        #:  POST request without password should succeed when
        #:  ALLOW_SEND_EMAIL_ON_REGISTER is True
        url = '/api/v1.1/auth/register/'
        self.assertEqual(User.objects.count(), 0)
        self.assertEqual(Email.objects.count(), 0)
        resp = self.client.post(url, {"email": "johndoe@netsach.com"})
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(Email.objects.count(), 1)

    @override_settings(ALLOW_SEND_EMAIL_ON_REGISTER=True)
    def test_register_without_password(self):
        #:  POST request without password should succeed when
        #:  ALLOW_SEND_EMAIL_ON_REGISTER is True
        url = '/api/v1.1/auth/register/'
        self.assertEqual(User.objects.count(), 0)
        self.assertEqual(PasswordChangeToken.objects.count(), 0)
        resp = self.client.post(url, {"email": "johndoe@netsach.com"})
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(PasswordChangeToken.objects.count(), 1)
        self.assertEqual(User.objects.count(), 1)
        set_password_token = PasswordChangeToken.objects.first().uid

        change_pwd_url = '/api/v1.1/auth/change-password/'
        resp = self.client.post(
            change_pwd_url,
            {
                "email": "johndoe@netsach.com",
                "password_change_token": set_password_token,
                "password1": "mypassword",
                "password2": "mypassword",
            },
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        #:  Try to login to make sure the new password is successfully set
        resp = self.client.post(
            '/api/v1.1/auth/login/',
            {"email": "johndoe@netsach.com", "password": "mypassword"},
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    @override_settings(ALLOW_SEND_EMAIL_ON_REGISTER=True)
    def test_register_without_password_url_format(self):
        url = '/api/v1.1/auth/register/'
        self.assertEqual(User.objects.count(), 0)

        #:  Wrong url_format
        resp = self.client.post(
            url,
            {
                "email": "johndoe@netsach.com",
                "url_format": "confirm/register/{first_arg}/{secod_arg}",
            },
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

        #:  Correct url_format
        resp = self.client.post(
            url,
            {
                "email": "johndoe@netsach.com",
                "url_format": "confirm/register/{token}/{email}",
            },
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.count(), 1)

    @override_settings(
        ALLOW_SEND_EMAIL_ON_REGISTER=True,
        AUTH_CONFIRM_EMAIL_DEFAULT_REDIRECT_TO="https://netsach.com",
    )
    def test_register_url_format_security_issues(self):
        url_register = '/api/v1.1/auth/register/'
        self.assertEqual(User.objects.count(), 0)

        #:  Create a superuser to perform authenticated requests
        superuser = User.objects.create_user('superuser@netsach.com')
        superuser.set_password('plop')
        superuser.set_level('superuser')
        superuser.save()
        UserConfirmation.objects.create(user=superuser, confirmed=True)

        url_login = '/api/v1.1/auth/login/'
        resp = self.client.post(
            url_login, {"email": "superuser@netsach.com", "password": "plop"}
        )
        super_token = resp.data['token']
        resp = self.client.post(
            url_register,
            {
                "email": "johndoe@netsach.com",
                "url_format": '{token.__class__.__init__.__globals__}/{email}',
            },
            HTTP_AUTHORIZATION='Token {}'.format(super_token),
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

        resp = self.client.post(
            url_register,
            {
                "email": "johndoe@netsach.com",
                "url_format": '{token.__class__.__init__.__globals__}/{email}/{token}',
            },
            HTTP_AUTHORIZATION='Token {}'.format(super_token),
        )
        #:  This case is not a problem since the {token.__class__.__init__.__globals__}
        #:  will be kept as it is and won't be formatted
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

    @override_settings(
        ALLOW_SEND_EMAIL_ON_REGISTER=True,
        AUTH_CONFIRM_EMAIL_DEFAULT_REDIRECT_TO="https://netsach.com",
    )
    def test_register_without_password_email_format_user_levels(self):
        url_register = '/api/v1.1/auth/register/'
        self.assertEqual(User.objects.count(), 0)

        #:  AnonymousUser cannot set an email format
        resp = self.client.post(
            url_register,
            {
                "email": "johndoe@netsach.com",
                "email_format": (
                    "<h1>Hello</h1>, <p>please click <a rel='notrack' "
                    "href='{link}'>here</a> to complete your registration</p>"
                ),
            },
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

        url_login = '/api/v1.1/auth/login/'
        #:  Create a simpleuser to perform authenticated requests
        simpleuser = User.objects.create_user('simpleuser@netsach.com')
        simpleuser.set_password('plop')
        simpleuser.save()
        UserConfirmation.objects.create(user=simpleuser, confirmed=True)
        resp = self.client.post(
            url_login, {"email": "simpleuser@netsach.com", "password": "plop"}
        )
        simple_token = resp.data['token']

        #:  Create a manager to perform authenticated requests
        manager = User.objects.create_user('manager@netsach.com')
        manager.set_password('plop')
        manager.set_level('manager')
        manager.save()
        UserConfirmation.objects.create(user=manager, confirmed=True)
        resp = self.client.post(
            url_login, {"email": "manager@netsach.com", "password": "plop"}
        )
        manager_token = resp.data['token']

        #:  a simple user cannot set an email format
        resp = self.client.post(
            url_register,
            {
                "email": "johndoe1@netsach.com",
                "url_format": "confirm/register/{token}/{email}",
                "email_format": (
                    "<h1>Hello</h1><br> <p>please click <a rel='notrack' "
                    "href='{link}'>here</a> to complete your registration</p>"
                ),
            },
            HTTP_AUTHORIZATION='Token {}'.format(simple_token),
        )
        self.assertEqual(
            resp.status_code, status.HTTP_400_BAD_REQUEST, msg=resp.content
        )

        #:  a user at least staff (manager for example) can set an email format
        resp = self.client.post(
            url_register,
            {
                "email": "johndoe2@netsach.com",
                "url_format": "confirm/register/{token}/{email}",
                "email_format": (
                    "<h1>Hello</h1><br> <p>please click <a rel='notrack' "
                    "href='{link}'>here</a> to complete your registration</p>"
                ),
            },
            HTTP_AUTHORIZATION='Token {}'.format(manager_token),
        )
        self.assertEqual(
            resp.status_code, status.HTTP_201_CREATED, msg=resp.content
        )

    @override_settings(
        ALLOW_SEND_EMAIL_ON_REGISTER=True,
        AUTH_CONFIRM_EMAIL_DEFAULT_REDIRECT_TO="https://netsach.com",
    )
    def test_register_without_password_email_format(self):
        url_register = '/api/v1.1/auth/register/'
        self.assertEqual(User.objects.count(), 0)

        #:  AnonymousUser cannot set an email format
        resp = self.client.post(
            url_register,
            {
                "email": "johndoe@netsach.com",
                "email_format": (
                    "<h1>Hello</h1>, <p>please click <a rel='notrack' "
                    "href='{link}'>here</a> to complete your registration</p>"
                ),
            },
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

        #:  Create a superuser to perform authenticated requests
        superuser = User.objects.create_user('superuser@netsach.com')
        superuser.set_password('plop')
        superuser.is_superuser = True
        superuser.save()
        UserConfirmation.objects.create(user=superuser, confirmed=True)
        url_login = '/api/v1.1/auth/login/'
        resp = self.client.post(
            url_login, {"email": "superuser@netsach.com", "password": "plop"}
        )
        super_token = resp.data['token']

        resp = self.client.post(
            url_register,
            {
                "email": "johndoe@netsach.com",
                "url_format": "confirm/register/{token}/{email}",
                "email_format": (
                    "<h1>Hello</h1><br> <p>please click <a rel='notrack' "
                    "href='{link}'>here</a> to complete your registration</p>"
                ),
            },
            HTTP_AUTHORIZATION='Token {}'.format(super_token),
        )
        self.assertEqual(
            resp.status_code, status.HTTP_201_CREATED, msg=resp.content
        )
        self.assertEqual(Email.objects.count(), 1)
        self.assertEqual(PasswordChangeToken.objects.count(), 1)
        token_set_passord = PasswordChangeToken.objects.first()
        expected_email_body = (
            "<h1>Hello</h1><br> <p>please click <a rel='notrack' href="
            f"'https://netsach.com/confirm/register/{token_set_passord.uid}/"
            "johndoe@netsach.com'>here</a> to complete your registration</p>"
        )
        email = Email.objects.first()
        self.assertEqual(email.body, expected_email_body)

    @override_settings(
        ALLOW_SEND_EMAIL_ON_REGISTER=True, AUTH_CONFIRM_EMAIL_ENABLE=True
    )
    def test_with_email_confirmation(self):
        url_register = '/api/v1.1/auth/register/'
        self.assertEqual(User.objects.count(), 0)
        self.assertEqual(Email.objects.count(), 0)
        self.assertEqual(UserConfirmation.objects.count(), 0)

        resp = self.client.post(url_register, {"email": "johndoe@netsach.com"})
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.count(), 1)
        user = User.objects.get(email='johndoe@netsach.com')

        #:  Check user is not confirmed
        self.assertFalse(user.is_confirmed())
        self.assertEqual(UserConfirmation.objects.count(), 1)
        confirmation = UserConfirmation.objects.first()
        confirmation_link = f'/c/confirm-user-email/{confirmation.uid}'

        #:  Confirm user by attempting a GET request on the confirmation link
        self.client.get(confirmation_link)
        self.assertTrue(user.is_confirmed())

        #:  Check that only one Email has been created (not two)
        self.assertEqual(Email.objects.count(), 1)


@override_settings(DEBUG=True)
class RegisterTestCase(APITestCase):
    def setUp(self):
        pass

    @override_settings(AUTH_CONFIRM_EMAIL_ENABLE=True)
    def test_register(self):

        url = '/api/v1.1/auth/register/'
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
        url = '/api/v1.1/auth/register/'
        # POST a non valid serializer (no field email)
        resp = self.client.post(
            url, {"password1": "mypassword", "password2": "mypasswordddd"}
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('_errors', resp.data)
        self.assertEqual(resp.data['_errors'], ['INVALID_DATA'])

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
        self.assertIn('_errors', resp.data)
        self.assertEqual(resp.data['_errors'], ['MISMATCH_PASSWORDS'])

    def test_register_with_custom_fields(self):
        url = '/api/v1.1/auth/register/'
        self.assertEqual(User.objects.count(), 0)

        resp = self.client.post(
            url,
            {
                "email": "johndoe@netsach.org",
                "password1": "mypassword",
                "password2": "mypassword",
                "first_name": "John",
                "last_name": "Doe",
            },
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.count(), 1)
        self.assertTrue(hasattr(resp, 'data'))
        self.assertIn('first_name', resp.data)
        self.assertEqual(resp.data['first_name'], 'John')
        self.assertIn('last_name', resp.data)
        self.assertEqual(resp.data['last_name'], 'Doe')

        created_user = User.objects.first()
        self.assertEqual(created_user.first_name, 'John')
        self.assertEqual(created_user.last_name, 'Doe')

    def test_register_with_wrong_fields(self):
        url = '/api/v1.1/auth/register/'
        self.assertEqual(User.objects.count(), 0)

        # POST data with a wrong field won't be considered
        resp = self.client.post(
            url,
            {
                "email": "johndoe@netsach.org",
                "password1": "mypassword",
                "password2": "mypassword",
                "some_fake_field": "some_fake_value",
                "first_name": "John",
            },
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.count(), 1)
        self.assertTrue(hasattr(resp, 'data'))
        self.assertNotIn('some_fake_field', resp.data)
        self.assertIn('first_name', resp.data)
        self.assertEqual(resp.data['first_name'], 'John')

        created_user = User.objects.first()
        self.assertFalse(hasattr(created_user, 'some_fake_field'))
        self.assertEqual(created_user.first_name, 'John')


@override_settings(DEBUG=True)
class RegisterTestCaseEmailLower(APITestCase):
    def setUp(self):
        pass

    def test_register_lower_case(self):

        url = '/api/v1.1/auth/register/'
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

    @override_settings(
        CONCRETE_REGISTER_BACKENDS=['tests.utils.TestRegisterBackend']
    )
    def test_register_backends(self):
        #: Create a Village instance that will be deleted by the backend
        Village.objects.create()
        self.assertEqual(Village.objects.count(), 1)

        url = '/api/v1.1/auth/register/'
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
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(resp.data.get('email'), email_lower)
        self.assertEqual(resp.data.get('level'), 'manager')
        self.assertEqual(Village.objects.count(), 0)


@override_settings(
    DEBUG=True, API_REGISTER_EMAIL_FILTER=r'.*@netsach\.(fr|org)'
)
class RegisterTestCaseEmailFilter(APITestCase):
    def setUp(self):
        pass

    def test_register_email_fr(self):

        url = '/api/v1.1/auth/register/'
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

        url = '/api/v1.1/auth/register/'
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
        self.assertEqual(
            resp.status_code, status.HTTP_201_CREATED, msg=resp.content
        )
        self.assertIn('token', resp.data)
        self.assertIn('email', resp.data)
        self.assertIn('first_name', resp.data)
        self.assertIn('last_name', resp.data)
        self.assertEqual(User.objects.count(), 1)

    def test_register_error_case(self):
        url = '/api/v1.1/auth/register/'
        # POST an incorrect domain name
        resp = self.client.post(
            url,
            {
                "email": "johndoe@namedomain.com",
                "password1": "mypassword",
                "password2": "mypassword",
            },
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('_errors', resp.data)
        self.assertEqual(
            resp.data['_errors'], ['EMAIL_NOT_AUTHORIZED_TO_REGISTER']
        )
        resp = self.client.post(
            url,
            {
                "email": "johndoe@namedomain.com",
                "password1": "123",
                "password2": "123",
            },
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('_errors', resp.data)
        self.assertEqual(resp.data['_errors'], ['NOT_ENOUGH_CHARS'])


@override_settings(DEBUG=True, ENABLE_USERS_SELF_REGISTER=False)
class RegisterTestCaseEnableUsersSelf(APITestCase):
    def setUp(self):
        pass

    def test_register(self):

        url = '/api/v1.1/auth/register/'

        # POST informations to register a new user

        # POST correct informations
        email = "johndoe@netsach.org"
        resp = self.client.post(
            url,
            {
                "email": email,
                "password1": "mypassword",
                "password2": "mypassword",
            },
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(resp.data['message'], 'Self register is not allowed')
        self.assertEqual(
            resp.data['_errors'], ['NOT_ALLOWED_TO_SELF_REGISTER']
        )
