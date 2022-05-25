from django.core.management import call_command
from django.core.management.base import CommandError

from django.test import TestCase

from concrete_datastore.concrete.models import User, Email


class ResetPasswordCommandManagementTests(TestCase):
    def setUp(self):
        self.super_user = User.objects.create_user(
            email='super_user@netsach.org', password='plop'
        )
        self.super_user.is_superuser = True
        self.super_user.save()

    def test_reset_password_super_user(self):
        self.assertEqual(self.super_user.check_password("plop"), True)
        call_command('reset_password', self.super_user.email)
        email_sent = Email.objects.get(created_by=self.super_user)
        self.super_user.refresh_from_db()

        self.assertEqual(1, Email.objects.all().count())
        self.assertIn("You have requested a new password", email_sent.body)
        self.assertEqual("Reset password on concrete", email_sent.subject)
        self.assertEqual(self.super_user.check_password("plop"), False)

    def test_reset_password_email_does_not_exist(self):
        resp = call_command('reset_password', "anonymous@netsach.org")
        self.assertEqual(0, Email.objects.all().count())
        self.assertEqual(resp, 'This email does not exists')

    def test_reset_password_email_is_none(self):
        with self.assertRaises(CommandError):
            call_command('reset_password')

        self.assertEqual(0, Email.objects.all().count())
