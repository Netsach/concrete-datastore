# coding: utf-8
from django.test import TestCase
from django.contrib.admin.sites import AdminSite
from concrete_datastore.admin.admin_form import (
    MyChangeUserForm,
    MyCreationUserForm,
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

    def test_creation_user(self):
        test_creation_form = MyCreationUserForm(
            {
                "email": "bbb@netsach.org",
                "password1": "test",
                "password2": "test",
            },
            instance=self.user,
        )
        test_creation_form.save()

    @override_settings(
        PASSWORD_MIN_SPECIAL=1,
    )
    def test_creation_user(self):
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
    def test_creation_user(self):
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
