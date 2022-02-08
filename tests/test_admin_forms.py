# coding: utf-8
from django.test import TestCase
from django.contrib.admin.sites import AdminSite
from concrete_datastore.admin.admin_form import (
    MyChangeUserForm,
    MyCreationUserForm,
    OTPAuthenticationForm,
)
from concrete_datastore.concrete.models import User
from django.test import override_settings


@override_settings(DEBUG=True)
class MyChangeUserFormTests(TestCase):
    def setUp(self):
        self.user = User.objects.create(email='aaa@netsach.org')
        self.site = AdminSite()

    def test_simple_user(self):
        test_user = User.objects.get(email="aaa@netsach.org")
        MyChangeUserForm({"email": "aaa@netsach.org"}, instance=test_user)

    def test_super_user(self):
        test_user = User.objects.get(email="aaa@netsach.org")
        test_user.is_superuser = True
        MyChangeUserForm({"email": "aaa@netsach.org"}, instance=test_user)

    def test_admin(self):
        test_user = User.objects.get(email="aaa@netsach.org")
        test_user.admin = True
        MyChangeUserForm({"email": "aaa@netsach.org"}, instance=test_user)

    def test_staff(self):
        test_user = User.objects.get(email="aaa@netsach.org")
        test_user.is_staff = True
        MyChangeUserForm({"email": "aaa@netsach.org"}, instance=test_user)

    def test_active(self):
        test_user = User.objects.get(email="aaa@netsach.org")
        test_user.is_active = True
        MyChangeUserForm({"email": "aaa@netsach.org"}, instance=test_user)

    def test_blocked(self):
        test_user = User.objects.get(email="aaa@netsach.org")
        test_user.is_active = False
        MyChangeUserForm({"email": "aaa@netsach.org"}, instance=test_user)


@override_settings(DEBUG=True)
class MyCreationUserFormTest(TestCase):
    def setUp(self):
        self.user = User.objects.create(email='aaa@netsach.org')
        self.site = AdminSite()

    def test_creation_user_nominal_behaviour(self):
        self.assertEqual(self.user.email, 'aaa@netsach.org')
        test_creation_form = MyCreationUserForm(
            {
                "email": "bbb@netsach.org",
                "password1": "test@",
                "password2": "test@",
            },
            instance=self.user,
        )
        test_creation_form.is_valid()
        test_creation_form.save(commit=True)
        self.assertEqual(self.user.email, 'bbb@netsach.org')

    @override_settings(PASSWORD_MIN_SPECIAL=1)
    def test_creation_user_special_char(self):
        test_creation_form = MyCreationUserForm(
            {
                "email": "bbb@netsach.org",
                "password1": "test@",
                "password2": "test@",
            },
            instance=self.user,
        )
        self.assertTrue(test_creation_form.is_valid())

    @override_settings(
        PASSWORD_MIN_SPECIAL=1, SPECIAL_CHARACTERS="!@#$%%^&*()_+-=[]{}|'\""
    )
    def test_creation_user_error(self):
        test_creation_form = MyCreationUserForm(
            {
                "email": "bbb@netsach.org",
                "password1": "test",
                "password2": "test",
            },
            instance=self.user,
        )
        self.assertFalse(test_creation_form.is_valid())
        self.assertNotEqual(str(test_creation_form.errors), '')


@override_settings(DEBUG=True)
class MfaAdmintestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create(email='test@netsach.org')
        self.user.set_password('test')
        self.user.set_level('superuser')
        self.user.save()

    def test_device_choices(self):
        device_choices = OTPAuthenticationForm.device_choices(self.user)
        device, _ = self.user.emaildevice_set.get_or_create(
            email=self.user.email, name='User default email', confirmed=True
        )
        self.assertListEqual(
            device_choices, [(device.persistent_id, device.name)]
        )

    def test_mfa_authentication_form(self):
        wrong_mfa_form = OTPAuthenticationForm(
            data={"username": "test@netsach.org", "password": "test"}
        )
        self.assertFalse(wrong_mfa_form.is_valid())
        device, _ = self.user.emaildevice_set.get_or_create(
            email=self.user.email, name='User default email', confirmed=True
        )
        code = device.generate_challenge()
        correct_mfa_form = OTPAuthenticationForm(
            data={
                "username": "test@netsach.org",
                "password": "test",
                "otp_token": code,
            }
        )
        self.assertTrue(correct_mfa_form.is_valid())

    @override_settings(TWO_FACTOR_CODE_TIMEOUT_SECONDS='test')
    def test_force_generate_challenge_error(self):
        #: setting TWO_FACTOR_CODE_TIMEOUT_SECONDS to a tring will raise
        #: an exception when generating challenge
        correct_mfa_form = OTPAuthenticationForm(
            data={"username": "test@netsach.org", "password": "test"}
        )
        self.assertFalse(correct_mfa_form.is_valid())

    def test_simpleuser_authenticate(self):
        user = User.objects.create(email='testsimple@netsach.org')
        user.set_password('test')
        user.save()
        correct_mfa_form = OTPAuthenticationForm(data={})
        self.assertFalse(correct_mfa_form.is_valid())
