from django.core.management import call_command
from django.core.management.base import CommandError

from django.test import TestCase

from concrete_datastore.concrete.models import User, Email


class ResetPasswordCommandManagementTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='johndoe@netsach.org', password='plop'
        )
        self.user.save()

    def test_reset_password_user(self):
        self.assertEqual(self.user.check_password("plop"), True)
        call_command('reset_password', self.user.email)
        email_sent = Email.objects.get(created_by=self.user)
        self.user.refresh_from_db()

        self.assertEqual(1, Email.objects.all().count())
        self.assertIn("You have requested a new password", email_sent.body)
        self.assertEqual("Reset password on concrete", email_sent.subject)
        self.assertEqual(self.user.check_password("plop"), False)

    def test_reset_password_email_does_not_exist(self):
        resp = call_command('reset_password', "anonymous@netsach.org")
        self.assertEqual(Email.objects.all().count(), 0)
        self.assertEqual(resp, 'This email does not exists')

    def test_reset_password_email_is_none(self):
        with self.assertRaises(CommandError):
            call_command('reset_password')

        self.assertEqual(Email.objects.all().count(), 0)
