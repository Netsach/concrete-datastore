# coding: utf-8
from django.test import TestCase
from concrete_datastore.concrete.models import (
    User,
    Group,
    DefaultDivider,
    Category,
    InstancePermission,
)


class CommunPermissionInstanceTestCase(TestCase):
    def setUp(self):
        self.simple = User.objects.create_user(
            email='simple@netsach.org', password='simple'
        )

        self.simple.set_level('simple', commit=True)
        url = '/api/v1/auth/login/'
        resp = self.client.post(
            url, {"email": "simple@netsach.org", "password": "simple"}
        )
        self.simple_token = resp.data['token']

        self.manager = User.objects.create_user(
            email='manager@netsach.org', password='manager'
        )

        self.manager.set_level('manager', commit=True)
        url = '/api/v1/auth/login/'
        resp = self.client.post(
            url, {"email": "manager@netsach.org", "password": "manager"}
        )
        self.manager_token = resp.data['token']

        self.admin = User.objects.create_user(
            email='admin@netsach.org', password='admin'
        )

        self.admin.set_level('admin', commit=True)
        url = '/api/v1/auth/login/'
        resp = self.client.post(
            url, {"email": "admin@netsach.org", "password": "admin"}
        )
        self.admin_token = resp.data['token']

        self.group_can_admin = Group.objects.create(
            name="Group for administration"
        )
        self.group_can_admin.members.set([self.manager.uid, self.admin.uid])

        self.divider = DefaultDivider.objects.create(name='divider')

        self.category1 = Category.objects.create(
            name='v1', defaultdivider=self.divider
        )
        self.category1.can_admin_groups.set([self.group_can_admin.uid])
        self.category1.can_view_users.set([self.simple.pk])
        self.category2 = Category.objects.create(
            name='v2', defaultdivider=self.divider
        )
        self.category2.can_admin_groups.set([self.group_can_admin.uid])
        self.category2.can_admin_users.set([self.simple.pk])

        self.category3 = Category.objects.create(
            name='v3', defaultdivider=self.divider
        )
        self.category3.can_admin_groups.set([self.group_can_admin.uid])

        self.simple.defaultdividers.add(self.divider)
        self.manager.defaultdividers.add(self.divider)
        self.admin.defaultdividers.add(self.divider)

        self.simple.save()
        self.manager.save()
        self.admin.save()

    def test_instance_permission(self):
        #: We expect 2 InstancePermissions: one for the simple and one for the
        #: manager
        self.assertEqual(InstancePermission.objects.count(), 2)
        self.assertTrue(
            InstancePermission.objects.filter(user_id=self.simple.pk).exists()
        )
        self.assertTrue(
            InstancePermission.objects.filter(user_id=self.manager.pk).exists()
        )
        simple_permissions = InstancePermission.objects.get(
            user_id=self.simple.pk
        )
        manager_permissions = InstancePermission.objects.get(
            user_id=self.manager.pk
        )

        simple_read_permissions = simple_permissions.read_instance_uids
        self.assertIn(str(self.category1.pk), simple_read_permissions)
        self.assertIn(str(self.category2.pk), simple_read_permissions)
        self.assertNotIn(str(self.category3.pk), simple_read_permissions)

        simple_write_permissions = simple_permissions.write_instance_uids
        self.assertNotIn(str(self.category1.pk), simple_write_permissions)
        self.assertIn(str(self.category2.pk), simple_write_permissions)
        self.assertNotIn(str(self.category3.pk), simple_write_permissions)

        manager_read_permissions = manager_permissions.read_instance_uids
        self.assertIn(str(self.category1.pk), manager_read_permissions)
        self.assertIn(str(self.category2.pk), manager_read_permissions)
        self.assertIn(str(self.category3.pk), manager_read_permissions)

        manager_write_permissions = manager_permissions.write_instance_uids
        self.assertIn(str(self.category1.pk), manager_write_permissions)
        self.assertIn(str(self.category2.pk), manager_write_permissions)
        self.assertIn(str(self.category3.pk), manager_write_permissions)

        self.group_can_admin.members.add(self.simple)
        simple_permissions.refresh_from_db()

        simple_read_permissions = simple_permissions.read_instance_uids
        self.assertIn(str(self.category1.pk), simple_read_permissions)
        self.assertIn(str(self.category2.pk), simple_read_permissions)
        self.assertIn(str(self.category3.pk), simple_read_permissions)

        simple_write_permissions = simple_permissions.write_instance_uids
        self.assertIn(str(self.category1.pk), simple_write_permissions)
        self.assertIn(str(self.category2.pk), simple_write_permissions)
        self.assertIn(str(self.category3.pk), simple_write_permissions)

        self.group_can_admin.members.remove(self.manager)
        manager_permissions.refresh_from_db()
        manager_read_permissions = manager_permissions.read_instance_uids
        self.assertIn(str(self.category1.pk), manager_read_permissions)
        self.assertIn(str(self.category2.pk), manager_read_permissions)
        self.assertIn(str(self.category3.pk), manager_read_permissions)

        manager_write_permissions = manager_permissions.write_instance_uids
        self.assertIn(str(self.category1.pk), manager_write_permissions)
        self.assertIn(str(self.category2.pk), manager_write_permissions)
        self.assertIn(str(self.category3.pk), manager_write_permissions)

        self.manager.defaultdividers.clear()
        manager_permissions.refresh_from_db()
        manager_read_permissions = manager_permissions.read_instance_uids
        self.assertNotIn(str(self.category1.pk), manager_read_permissions)
        self.assertNotIn(str(self.category2.pk), manager_read_permissions)
        self.assertNotIn(str(self.category3.pk), manager_read_permissions)

        manager_write_permissions = manager_permissions.write_instance_uids
        self.assertNotIn(str(self.category1.pk), manager_write_permissions)
        self.assertNotIn(str(self.category2.pk), manager_write_permissions)
        self.assertNotIn(str(self.category3.pk), manager_write_permissions)


class CanViewAdminUsersTestCase(TestCase):
    def setUp(self):
        self.u_1 = User.objects.create_user(
            email='user1@netsach.org', password='simple'
        )
        self.u_2 = User.objects.create_user(
            email='user2@netsach.org', password='simple'
        )
        self.u_3 = User.objects.create_user(
            email='user3@netsach.org', password='simple'
        )
        self.u_4 = User.objects.create_user(
            email='user4@netsach.org', password='simple'
        )
        self.cat_1 = Category.objects.create(name='Cat 1')
        self.cat_2 = Category.objects.create(name='Cat 2')
        self.cat_3 = Category.objects.create(name='Cat 3')
        self.cat_4 = Category.objects.create(name='Cat 4')

    def test_set_can_view_admin_users(self):
        self.assertEqual(InstancePermission.objects.count(), 0)
        self.cat_1.can_view_users.set([self.u_1])
        self.assertEqual(InstancePermission.objects.count(), 1)

        permissions_instance_1 = InstancePermission.objects.first()
        self.assertEqual(permissions_instance_1.user_id, self.u_1.pk)
        self.assertEqual(permissions_instance_1.model_name, 'Category')
        self.assertListEqual(
            permissions_instance_1.read_instance_uids, [str(self.cat_1.pk)]
        )
        self.assertListEqual(permissions_instance_1.write_instance_uids, [])

        self.cat_1.can_view_users.set([self.u_2])
        self.assertEqual(InstancePermission.objects.count(), 2)
        permissions_instance_1.refresh_from_db()
        permissions_instance_2 = InstancePermission.objects.get(
            user_id=self.u_2.pk
        )
        self.assertListEqual(permissions_instance_1.read_instance_uids, [])
        self.assertListEqual(permissions_instance_1.write_instance_uids, [])

        self.assertListEqual(
            permissions_instance_2.read_instance_uids, [str(self.cat_1.pk)]
        )
        self.assertListEqual(permissions_instance_2.write_instance_uids, [])

        self.cat_1.can_view_users.set([self.u_3, self.u_4])
        self.assertEqual(InstancePermission.objects.count(), 4)
        permissions_instance_1.refresh_from_db()
        permissions_instance_2.refresh_from_db()
        permissions_instance_3 = InstancePermission.objects.get(
            user_id=self.u_3.pk
        )
        permissions_instance_4 = InstancePermission.objects.get(
            user_id=self.u_4.pk
        )
        self.assertListEqual(permissions_instance_1.read_instance_uids, [])
        self.assertListEqual(permissions_instance_1.write_instance_uids, [])
        self.assertListEqual(permissions_instance_2.read_instance_uids, [])
        self.assertListEqual(permissions_instance_2.write_instance_uids, [])
        self.assertListEqual(
            permissions_instance_3.read_instance_uids, [str(self.cat_1.pk)]
        )
        self.assertListEqual(permissions_instance_3.write_instance_uids, [])
        self.assertListEqual(
            permissions_instance_4.read_instance_uids, [str(self.cat_1.pk)]
        )
        self.assertListEqual(permissions_instance_4.write_instance_uids, [])

        self.cat_2.can_view_users.set([self.u_3])
        self.cat_3.can_admin_users.set([self.u_4])

        permissions_instance_1.refresh_from_db()
        permissions_instance_2.refresh_from_db()
        permissions_instance_3.refresh_from_db()
        permissions_instance_4.refresh_from_db()
        self.assertListEqual(permissions_instance_1.read_instance_uids, [])
        self.assertListEqual(permissions_instance_1.write_instance_uids, [])
        self.assertListEqual(permissions_instance_2.read_instance_uids, [])
        self.assertListEqual(permissions_instance_2.write_instance_uids, [])
        self.assertSetEqual(
            set(permissions_instance_3.read_instance_uids),
            {str(self.cat_1.pk), str(self.cat_2.pk)},
        )
        self.assertListEqual(permissions_instance_3.write_instance_uids, [])
        self.assertSetEqual(
            set(permissions_instance_4.read_instance_uids),
            {str(self.cat_1.pk), str(self.cat_3.pk)},
        )
        self.assertListEqual(
            permissions_instance_4.write_instance_uids, [str(self.cat_3.pk)]
        )

    def test_set_can_view_admin_groups(self):
        self.assertEqual(InstancePermission.objects.count(), 0)
        g_v_1 = Group.objects.create(name='group viewer 1')
        g_v_2 = Group.objects.create(name='group viewer 2')
        g_a_1 = Group.objects.create(name='group admin 1')
        g_a_2 = Group.objects.create(name='group admin 2')

        self.cat_1.can_view_groups.add(g_v_1)
        self.cat_1.can_admin_groups.add(g_a_1)
        g_v_1.members.add(self.u_1)
        self.assertEqual(InstancePermission.objects.count(), 1)
        perm_1 = InstancePermission.objects.get(user_id=self.u_1.pk)
        self.assertListEqual([str(self.cat_1.pk)], perm_1.read_instance_uids)
        self.assertListEqual([], perm_1.write_instance_uids)
        g_a_1.members.add(self.u_2)
        self.assertEqual(InstancePermission.objects.count(), 2)
        perm_1.refresh_from_db()
        self.assertIn(str(self.cat_1.pk), perm_1.read_instance_uids)
        self.assertListEqual([], perm_1.write_instance_uids)
        perm_2 = InstancePermission.objects.get(user_id=self.u_2.pk)
        self.assertListEqual([str(self.cat_1.pk)], perm_2.read_instance_uids)
        self.assertListEqual([str(self.cat_1.pk)], perm_2.write_instance_uids)
        g_v_1.members.clear()
        perm_1.refresh_from_db()
        self.assertListEqual([], perm_1.read_instance_uids)
        self.assertListEqual([], perm_1.write_instance_uids)
        self.cat_1.can_admin_groups.clear()
        perm_2.refresh_from_db()
        self.assertListEqual([], perm_2.read_instance_uids)
        self.assertListEqual([], perm_2.write_instance_uids)
        self.cat_1.can_view_groups.add(g_v_1)
        self.cat_1.can_view_groups.add(g_v_2)
        g_v_1.members.set({self.u_1, self.u_2})
        self.u_3.concrete_groups.add(g_v_2)

        perm_1.refresh_from_db()
        self.assertListEqual([str(self.cat_1.pk)], perm_1.read_instance_uids)
        self.assertListEqual([], perm_1.write_instance_uids)
        perm_2.refresh_from_db()
        self.assertListEqual([str(self.cat_1.pk)], perm_2.read_instance_uids)
        self.assertListEqual([], perm_2.write_instance_uids)
        perm_3 = InstancePermission.objects.get(user_id=self.u_3.pk)
        self.assertListEqual([str(self.cat_1.pk)], perm_3.read_instance_uids)
        self.assertListEqual([], perm_3.write_instance_uids)
        g_a_2.members.set({self.u_1, self.u_2})
        self.cat_1.can_admin_groups.add(g_a_2)

        perm_1.refresh_from_db()
        self.assertListEqual([str(self.cat_1.pk)], perm_1.read_instance_uids)
        self.assertListEqual([str(self.cat_1.pk)], perm_1.write_instance_uids)
        perm_2.refresh_from_db()
        self.assertListEqual([str(self.cat_1.pk)], perm_2.read_instance_uids)
        self.assertListEqual([str(self.cat_1.pk)], perm_2.write_instance_uids)

        self.cat_1.can_admin_users.add(self.u_1)
        self.cat_1.can_admin_groups.clear()
        perm_1.refresh_from_db()
        self.assertListEqual([str(self.cat_1.pk)], perm_1.read_instance_uids)
        self.assertListEqual([str(self.cat_1.pk)], perm_1.write_instance_uids)
        perm_2.refresh_from_db()
        self.assertListEqual([str(self.cat_1.pk)], perm_2.read_instance_uids)
        self.assertListEqual([], perm_2.write_instance_uids)
