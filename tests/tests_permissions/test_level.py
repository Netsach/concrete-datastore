# coding: utf-8
from django.test import TestCase
from concrete_datastore.concrete.models import User
from django.test import override_settings


@override_settings(DEBUG=True)
class UserLeveleTest(TestCase):
    def test_set_get_level(self):
        u = User.objects.create(email='user@netsach.org')

        u.set_level('superuser', commit=True)
        u.refresh_from_db()

        self.assertTrue(u.is_superuser)
        self.assertTrue(u.admin)
        self.assertTrue(u.is_staff)
        self.assertTrue(u.is_active)
        self.assertEqual(u.level, 'superuser')
        self.assertEqual(u.get_level(), 'SuperUser')

        u.set_level('admin', commit=True)
        u.refresh_from_db()

        self.assertFalse(u.is_superuser)
        self.assertTrue(u.admin)
        self.assertTrue(u.is_staff)
        self.assertTrue(u.is_active)
        self.assertEqual(u.level, 'admin')
        self.assertEqual(u.get_level(), 'Admin')

        u.set_level('manager', commit=True)
        u.refresh_from_db()

        self.assertFalse(u.is_superuser)
        self.assertFalse(u.admin)
        self.assertTrue(u.is_staff)
        self.assertTrue(u.is_active)
        self.assertEqual(u.level, 'manager')
        self.assertEqual(u.get_level(), 'Manager')

        u.set_level('simpleuser', commit=True)
        u.refresh_from_db()

        self.assertFalse(u.is_superuser)
        self.assertFalse(u.is_staff)
        self.assertFalse(u.admin)
        self.assertTrue(u.is_active)
        self.assertEqual(u.level, 'simpleuser')
        self.assertEqual(u.get_level(), 'SimpleUser')

        u.set_level('blocked', commit=True)
        u.refresh_from_db()

        self.assertFalse(u.is_superuser)
        self.assertFalse(u.is_staff)
        self.assertFalse(u.admin)
        self.assertFalse(u.is_active)
        self.assertEqual(u.level, 'blocked')
        self.assertEqual(u.get_level(), 'Blocked')
