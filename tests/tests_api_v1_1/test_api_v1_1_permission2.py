# coding: utf-8

from mock import MagicMock
from rest_framework.test import APITestCase
from concrete_datastore.concrete.models import User
from concrete_datastore.api.v1.permissions import (
    UserAccessPermission,
    filter_queryset_by_divider,
    filter_queryset_by_permissions,
)
from concrete_datastore.api.v1.views import AccountMeApiView
from django.test import override_settings


@override_settings(DEBUG=True)
class PermissionTestCase(APITestCase):
    def test_class_name_in_undivided_model(self):
        obj = MagicMock()
        obj.__class__.__name__ = str('Fusee')
        self.assertTrue(
            UserAccessPermission().check_divider_permission(
                request=None, obj=obj
            )
        )

    def test_class_name_is_divider_model(self):
        obj = MagicMock()
        request = MagicMock()
        obj.pk = 1
        obj.__class__.__name__ = str('DefaultDivider')

        self.assertTrue(
            UserAccessPermission().check_divider_permission(
                request=request, obj=obj
            )
        )

    def test_has_permission(self):
        request = MagicMock()
        request.method = "OPTIONS"
        self.assertFalse(
            UserAccessPermission().has_permission(
                request=request, view=AccountMeApiView
            )
        )

    def test_has_object_permissions(self):
        obj = MagicMock(User)
        request = MagicMock()
        request.method = "OTHER_METHOD"
        self.assertFalse(
            UserAccessPermission().has_object_permission(
                request=request, view=AccountMeApiView, obj=obj
            )
        )

    def test_has_object_permissions_delete_method(self):
        obj = MagicMock(User)
        request = MagicMock()
        request.method = "DELETE"
        self.assertFalse(
            UserAccessPermission().has_object_permission(
                request=request, view=AccountMeApiView, obj=obj
            )
        )

    def test_filter_queryset_by_devider_superuser_or_admin(self):
        queryset = MagicMock()
        user = MagicMock()
        divider = MagicMock()
        user.is_authenticated = MagicMock(return_value=True)
        user.is_superuser = True
        self.assertIsInstance(
            filter_queryset_by_divider(
                queryset=queryset, user=user, divider=divider
            ),
            MagicMock,
        )
        self.assertIsInstance(
            filter_queryset_by_permissions(
                queryset=queryset, user=user, divider=divider
            ),
            MagicMock,
        )
        user.is_superuser = False
        user.admin = True
        self.assertIsInstance(
            filter_queryset_by_divider(
                queryset=queryset, user=user, divider=divider
            ),
            MagicMock,
        )

    def test_filter_queryset_by_permissions_exception(self):
        queryset = MagicMock()
        user = MagicMock()
        divider = MagicMock()
        user.is_authenticated = MagicMock(return_value=True)
        user.is_superuser = False
        user.is_admin = False
        user.is_staff = False
        queryset.filter().distinct = MagicMock(side_effect=Exception)
        filter_queryset_by_permissions(
            queryset=queryset, user=user, divider=divider
        )
