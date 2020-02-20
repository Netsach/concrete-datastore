# coding: utf-8
from django.test import TestCase
from django.contrib import admin
from django.test import override_settings

from concrete_datastore.admin.admin_models import MetaAdmin, MetaUserAdmin
from concrete_datastore.admin.admin_form import MyChangeUserForm
from concrete_datastore.concrete.models import User, Group


@override_settings(DEBUG=True)
class ModelAdminTest(TestCase):
    def setUp(self):
        self.user_a = User.objects.create_user(
            email="aaa@netsach.org", password='test'
        )
        self.user_a.is_superuser = True
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
        #     for meta_model in list_of_meta:
        #         if meta_model.get_model_name() == 'Group':
        #             my_class = meta_model

        #     if my_class:
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
