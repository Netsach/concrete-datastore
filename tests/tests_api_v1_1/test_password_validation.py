# coding: utf-8
from django.test import TestCase
from rest_framework import status
from concrete_datastore.concrete.models import User
from concrete_datastore.concrete.password import (
    PasswordMinLengthValidation,
    PasswordMinDigitsValidation,
    PasswordMinLowerValidation,
    PasswordMinUpperValidation,
)
from django.conf import settings
from django.test import override_settings


@override_settings(
    DEBUG=True,
    PASSWORD_MIN_LENGTH=4,
    PASSWORD_MIN_DIGITS=1,
    PASSWORD_MIN_LOWER=1,
    PASSWORD_MIN_UPPER=1,
)
class PasswordValidationTestCase(TestCase):
    def setUp(self):
        self.register_url = '/api/v1.1/auth/register/'

    def test_min_length(self):
        resp = self.client.post(
            self.register_url,
            {
                "email": "johndoe@netsach.com",
                "password1": "abc",
                "password2": "abc",
            },
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertDictEqual(
            resp.data,
            {
                "message": "The password must contain at least 4 character(s).",
                "_errors": ["NOT_ENOUGH_CHARS"],
            },
        )

    def test_min_digits(self):
        resp = self.client.post(
            self.register_url,
            {
                "email": "johndoe@netsach.com",
                "password1": "abcd",
                "password2": "abcd",
            },
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertDictEqual(
            resp.data,
            {
                "message": "The password must contain at least 1 digit(s).",
                "_errors": ["NOT_ENOUGH_DIGITS"],
            },
        )

    def test_min_upper(self):
        resp = self.client.post(
            self.register_url,
            {
                "email": "johndoe@netsach.com",
                "password1": "abcd1",
                "password2": "abcd1",
            },
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertDictEqual(
            resp.data,
            {
                "message": "The password must contain at least 1 upper character(s).",
                "_errors": ["NOT_ENOUGH_UPPER"],
            },
        )

    def test_min_lower(self):
        resp = self.client.post(
            self.register_url,
            {
                "email": "johndoe@netsach.com",
                "password1": "ABCD1",
                "password2": "ABCD1",
            },
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertDictEqual(
            resp.data,
            {
                "message": "The password must contain at least 1 lower character(s).",
                "_errors": ["NOT_ENOUGH_LOWER"],
            },
        )

    def test_proper_register(self):
        resp = self.client.post(
            self.register_url,
            {
                "email": "johndoe@netsach.com",
                "password1": "aBcD1",
                "password2": "aBcD1",
            },
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertIn('token', resp.data)
        self.assertIn('email', resp.data)
        self.assertIn('first_name', resp.data)
        self.assertIn('last_name', resp.data)
        self.assertEqual(User.objects.count(), 1)

    def test_get_help_message(self):
        help_text_length = PasswordMinLengthValidation().get_help_text()
        help_text_digit = PasswordMinDigitsValidation().get_help_text()
        help_text_lower = PasswordMinLowerValidation().get_help_text()
        help_text_upper = PasswordMinUpperValidation().get_help_text()
        self.assertEqual(
            help_text_length,
            "Your password must contain at least 4 character(s).",
        )
        self.assertEqual(
            help_text_digit, "Your password must contain at least 1 digit(s)."
        )
        self.assertEqual(
            help_text_lower,
            "Your password must contain at least 1 lower character(s).",
        )
        self.assertEqual(
            help_text_upper,
            "Your password must contain at least 1 upper character(s).",
        )

    @override_settings(
        PASSWORD_MIN_SPECIAL=1,
        PASSWORD_MIN_LENGTH=4,
        PASSWORD_MIN_DIGITS=0,
        PASSWORD_MIN_LOWER=0,
        PASSWORD_MIN_UPPER=0,
    )
    def test_min_special_success(self):

        register_url = '/api/v1/auth/register/'

        rsp = self.client.post(
            register_url,
            data={
                "email": 'aaaa@netsach.com',
                "password1": "Test#",
                "password2": "Test#",
            },
        )
        self.assertEqual(rsp.status_code, status.HTTP_201_CREATED)

    @override_settings(
        PASSWORD_MIN_SPECIAL=1,
        PASSWORD_MIN_LENGTH=4,
        PASSWORD_MIN_DIGITS=0,
        PASSWORD_MIN_LOWER=0,
        PASSWORD_MIN_UPPER=0,
    )
    def test_min_special_failure(self):

        register_url = '/api/v1/auth/register/'

        rsp = self.client.post(
            register_url,
            data={
                "email": 'aaaa@netsach.com',
                "password1": "Test",
                "password2": "Test",
            },
        )
        self.assertEqual(rsp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            rsp.data['message'],
            (
                "The password must contain at least 1 special"
                " character(s) from these : {special_list}"
            ).format(special_list=settings.SPECIAL_CHARACTERS),
        )
