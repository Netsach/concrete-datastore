from django.core.management import call_command
from django.core.management.base import CommandError


from django.test import TestCase

from concrete_datastore.concrete.models import User, Email


class CreateSuperUserWithEmailTests(TestCase):
    def setUp(self):
        self.super_user = User.objects.create_user(
            email='super_user@netsach.org', password='plop'
        )
        self.super_user.save()

    def test_create_superuser(self):
        self.assertEqual(User.objects.all().count(), 1)
        call_command(
            'create_superuser_with_email', "new_superuser@netsach.org"
        )
        new_superuser = User.objects.get(email="new_superuser@netsach.org")
        email_sent = Email.objects.get(created_by=new_superuser)

        self.assertEqual(Email.objects.all().count(), 1)
        self.assertEqual(User.objects.all().count(), 2)

        self.assertIn("Welcome to Concrete", email_sent.body)
        self.assertEqual(new_superuser.level, "superuser")
        self.assertTrue(new_superuser.admin)
        self.assertEqual("Access to Concrete Instance", email_sent.subject)

    def test_create_superuser_email_exists(self):
        self.assertEqual(1, User.objects.all().count())

        resp = call_command(
            'create_superuser_with_email', self.super_user.email
        )
        self.assertEqual(resp, "This email is already used")
        self.assertEqual(Email.objects.all().count(), 0)
        self.assertEqual(User.objects.all().count(), 1)

    def test_create_superuser_email_is_none(self):
        with self.assertRaises(CommandError):
            call_command('create_superuser_with_email')

        self.assertEqual(0, Email.objects.all().count())
