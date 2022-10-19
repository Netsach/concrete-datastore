# coding: utf-8
from django.core.management import call_command
from django.core.management.base import CommandError


from django.test import TestCase

from concrete_datastore.concrete.models import User


class CreateSuperUserTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='johndoe@netsach.org', password='plop'
        )
        self.user.save()

    def test_create_superuser(self):
        self.assertEqual(User.objects.all().count(), 1)
        call_command("create_superuser", "new_superuser@netsach.org", "plop")
        new_superuser = User.objects.get(email="new_superuser@netsach.org")

        self.assertEqual(User.objects.all().count(), 2)

        self.assertEqual(new_superuser.level, "superuser")
        self.assertTrue(new_superuser.admin)
        self.assertTrue(new_superuser.check_password("plop"))

    def test_create_superuser_email_already_exist(self):
        self.assertEqual(User.objects.all().count(), 1)
        call_command("create_superuser", "johndoe@netsach.org", "plop")

        self.assertEqual(User.objects.all().count(), 1)

    def test_create_superuser_args_are_none(self):
        with self.assertRaises(CommandError) as e:
            call_command('create_superuser')
        self.assertEqual(
            str(e.exception),
            "Error: the following arguments are required: email, password",
        )
