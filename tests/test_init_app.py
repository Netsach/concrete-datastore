# coding: utf-8
from django.core.management import call_command
from django.test import TestCase
import concrete_datastore
from concrete_datastore.concrete.models import (
    Project,
    User,
    InstancePermission,
    SystemVersion,
)


class CommunPermissionInstanceTestCase(TestCase):
    def test_empty_db(self):
        self.assertEqual(SystemVersion.objects.count(), 0)
        self.assertEqual(InstancePermission.objects.count(), 0)
        call_command('init_app')
        self.assertEqual(SystemVersion.objects.count(), 2)
        self.assertEqual(InstancePermission.objects.count(), 0)
        datastore_version = SystemVersion.objects.get(
            app_name='concrete_datastore'
        )
        self.assertEqual(
            datastore_version.version, concrete_datastore.__version__
        )
        self.assertTrue(datastore_version.is_latest)
        datamodel_version = SystemVersion.objects.get(app_name='datamodel')
        self.assertEqual(datamodel_version.version, '1.0.0')
        self.assertTrue(datamodel_version.is_latest)

    def test_with_users(self):
        self.assertEqual(InstancePermission.objects.count(), 0)
        simple = User.objects.create(email="simple@netsach.org")
        manager = User.objects.create(email="manager@netsach.org")
        manager.set_level('manager')
        manager.save()
        admin = User.objects.create(email="admin@netsach.org")
        admin.set_level('admin')
        admin.save()
        superuser = User.objects.create(email="superuser@netsach.org")
        superuser.set_level('superuser')
        superuser.save()
        #: No InstancePermission because the dabase is empty
        self.assertEqual(InstancePermission.objects.count(), 0)

        #: Create a project
        Project.objects.create()
        self.assertEqual(InstancePermission.objects.count(), 0)
        call_command('init_app')
        #: We expect 2 InstancePermissions: simple + manager
        self.assertEqual(InstancePermission.objects.count(), 2)
        self.assertEqual(
            InstancePermission.objects.filter(user_id=simple.pk).count(), 1
        )
        self.assertEqual(
            InstancePermission.objects.filter(user_id=manager.pk).count(), 1
        )

        #: If we update the admin level to manager, we expect a new
        #: InstancePermission
        admin.set_level('manager')
        admin.save()
        self.assertEqual(InstancePermission.objects.count(), 3)
        self.assertEqual(
            InstancePermission.objects.filter(user_id=admin.pk).count(), 1
        )

        #: If we create a new simpleUser, we expect a new InstancePermission
        simple2 = User.objects.create(email="simple2@netsach.org")
        self.assertEqual(InstancePermission.objects.count(), 4)
        self.assertEqual(
            InstancePermission.objects.filter(user_id=simple2.pk).count(), 1
        )
