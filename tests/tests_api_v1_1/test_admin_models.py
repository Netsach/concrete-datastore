# coding: utf-8
from django.test import TestCase, Client
from django.contrib import admin
from django.test import override_settings
from django.http import StreamingHttpResponse

from concrete_datastore.admin.admin_models import MetaAdmin, MetaUserAdmin
from concrete_datastore.admin.admin import ConcreteRoleAdmin, admin_site
from concrete_datastore.admin.admin_form import MyChangeUserForm
from concrete_datastore.concrete.models import User, Group, ConcreteRole


@override_settings(DEBUG=True)
class ModelAdminTest(TestCase):
    def setUp(self):
        self.user_a = User.objects.create_user(email="aaa@netsach.org")
        self.user_a.set_level('superuser')
        self.user_a.set_password('test')
        self.user_a.save()
        self.site = admin.site

        class MockRequest(object):
            user = self.user_a

        self.request = MockRequest()

    @override_settings(
        ADMIN_SHOW_USER_PERMISSIONS=True, AUTH_CONFIRM_EMAIL_ENABLE=False
    )
    def test_create_user_with_MetaUserAdmin(self):
        user = User.objects.create(email="test_user@netsach.org")

        class TestMetaUserAdmin(MetaUserAdmin):
            class Meta:
                model = User

        self.request.user = self.user_a
        user_model = TestMetaUserAdmin(User, self.site)
        user_model.save_model(
            self.request, user, user_model.get_form(self.request), change=False
        )
        self.assertIs(user.is_confirmed(), True)

    @override_settings(AUTH_CONFIRM_EMAIL_ENABLE=True)
    def test_create_entity(self):
        group = Group.objects.create(name="group test")

        class GroupMetaAdmin(MetaAdmin):
            class Meta:
                model = Group

        self.request.user = self.user_a
        group_model = GroupMetaAdmin(Group, self.site)
        group_model.save_model(
            self.request,
            group,
            group_model.get_form(self.request),
            change=False,
        )

        self.assertEqual(group.created_by, self.user_a)
        self.assertEqual(group.name, "group test")

        user_b = User.objects.create_user(
            email="bbb@netsach.org", password='test'
        )
        user_b.is_superuser = True
        user_b.save()
        user_change_model = MetaAdmin(User, self.site)
        group.name = "new name"
        data = {}
        for elt in user_change_model.get_fields(self.request):
            field = getattr(user_b, elt, None)
            if field:
                data.update({elt: field})
        # data.update({"password": "testB"})
        my_form = group_model.get_form(self.request)(instance=group, data=data)
        my_form.is_valid()
        user_change_model.save_model(
            request=self.request, obj=group, form=my_form, change=True
        )

        self.assertEqual(group.created_by, self.user_a)
        self.assertEqual(group.name, "new name")

    @override_settings(AUTH_CONFIRM_EMAIL_ENABLE=True)
    def test_user_modification(self):
        class UserModelTest(MetaUserAdmin):
            form = MyChangeUserForm

            class Meta:
                model = User
                fields = ("user_level",)

        user_b = User.objects.create_user(
            email='bbb@netsach.org', password='testB'
        )
        self.assertIs(user_b.admin, False)
        user_change_model = UserModelTest(User, self.site)
        data = {'user_level': 'Admin'}
        for elt in user_change_model.get_fields(self.request):
            field = getattr(user_b, elt, None)
            if field:
                data.update({elt: field})
        data.update({"password": "testB"})
        my_form = MyChangeUserForm(instance=user_b, data=data)
        my_form.is_valid()
        user_change_model.save_model(
            request=self.request, obj=user_b, form=my_form, change=True
        )
        self.assertIs(user_b.admin, True)

    def test_get_list_users(self):
        client = Client()
        client.login(username='aaa@netsach.org', password='test')
        resp = client.get('/concrete-datastore-admin/user/')
        self.assertEqual(resp.status_code, 200)

    def test_export_csv_admin_site(self):
        client = Client()
        client.login(username='aaa@netsach.org', password='test')
        resp = client.get('/concrete-datastore-admin/user/')
        self.assertEqual(resp.status_code, 200)
        data = {
            'action': 'export_csv',
            '_selected_action': list(
                User.objects.values_list('pk', flat=True)
            ),
        }
        resp = client.post('/concrete-datastore-admin/user/', data)
        self.assertTrue(isinstance(resp, StreamingHttpResponse))

    def test_save_mixin(self):
        obj = ConcreteRole()
        self.assertEqual(ConcreteRole.objects.count(), 0)
        concrete_role_admin = ConcreteRoleAdmin(
            model=ConcreteRole, admin_site=admin_site
        )
        concrete_role_admin.save_model(
            obj=obj, request=self.request, form=None, change=False
        )
        self.assertEqual(ConcreteRole.objects.count(), 1)
        concrete_role = ConcreteRole.objects.first()
        print(concrete_role.created_by)
        self.assertEqual(ConcreteRole.objects.first().users.count(), 0)
        concrete_role.users.add(self.user_a)
        concrete_role_admin.save_model(
            obj=concrete_role, request=self.request, form=None, change=True
        )
        self.assertEqual(ConcreteRole.objects.count(), 1)
        self.assertEqual(ConcreteRole.objects.first().users.count(), 1)
