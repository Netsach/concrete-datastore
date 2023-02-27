# coding: utf-8
from django.apps import apps
from django.conf import settings
from django.contrib.auth import get_user_model

from rest_framework.reverse import reverse
from rest_framework import serializers

from concrete_datastore.concrete.models import (
    DIVIDER_MODEL,
    ConcreteRole,
    ConcretePermission,
    EmailDevice,
)
from concrete_datastore.api.v1 import DEFAULT_API_NAMESPACE
from concrete_datastore.api.v1.serializers import make_serializer_class
from concrete_datastore.api.v1.signals import build_absolute_uri
from concrete_datastore.concrete.meta import get_meta_definition_by_model_name

concrete = apps.get_app_config('concrete')


class ProcessRegisterSerializer(serializers.Serializer):
    application = serializers.CharField(max_length=200, required=True)
    instance = serializers.CharField(max_length=200, required=True)
    token = serializers.UUIDField(required=True)


def make_account_me_serialier(api_namespace=DEFAULT_API_NAMESPACE):
    meta = get_meta_definition_by_model_name('User')
    meta_serializer_class = make_serializer_class(
        meta_model=meta, api_namespace=api_namespace, nested=False, safe=True
    )
    Meta = meta_serializer_class.Meta
    Meta.fields = [
        field
        for field in Meta.fields
        if field not in ['admin', 'is_staff', 'is_superuser', 'is_active']
    ] + ['level']

    Meta.read_only_fields = Meta.read_only_fields + [
        'uid',
        'public',
        'creation_date',
        'modification_date',
        '{}s'.format(DIVIDER_MODEL.lower()),
    ]

    serializer_attrs = {
        'Meta': Meta,
        'level': serializers.SerializerMethodField(),
        'get_level': lambda self, obj: obj.get_level(),
    }

    if settings.USE_CONCRETE_ROLES:
        Meta.fields = Meta.fields + ['roles', 'roles_uid']
        Meta.read_only_fields = Meta.read_only_fields + ['roles', 'roles_uid']
        serializer_attrs.update(
            {
                'roles': serializers.SerializerMethodField(),
                'get_roles': lambda self, obj: obj.get_roles(),
                'roles_uid': serializers.SerializerMethodField(),
                'get_roles_uid': lambda self, obj: obj.get_roles_uid(),
            }
        )
    return type(
        str('AccountMeSerializer'), (meta_serializer_class,), serializer_attrs
    )


class ConcreteRoleSerializer(serializers.ModelSerializer):
    UserModel = get_user_model()
    users_uid = serializers.PrimaryKeyRelatedField(
        source="users",
        many=True,
        required=False,
        queryset=UserModel.objects.all(),
    )
    url = serializers.SerializerMethodField()

    class Meta:
        model = ConcreteRole
        fields = (
            "uid",
            "name",
            "users_uid",
            "url",
            "created_by",
            "creation_date",
            "modification_date",
        )
        read_only_fields = (
            'uid',
            'users',
            'url',
            'created_by',
            'creation_date',
            'modification_date',
        )

    def get_url(self, obj):
        uri = reverse("api_v1_1:acl-role-detail", args=(obj.pk,))
        if hasattr(self, '_context'):
            if 'request' in self._context:
                request = self._context['request']
                return request.build_absolute_uri(uri)
        return build_absolute_uri(uri)  # skip-test-coverage


class EmailDeviceSerializer(serializers.ModelSerializer):

    url = serializers.SerializerMethodField()

    class Meta:
        model = EmailDevice
        fields = (
            "uid",
            "name",
            "email",
            "confirmed",
            "url",
            'user',
            "created_by",
            "creation_date",
            "modification_date",
        )
        read_only_fields = (
            'uid',
            'url',
            'user',
            'created_by',
            'creation_date',
            'modification_date',
        )

    def get_url(self, obj):
        uri = reverse("api_v1_1:email-device-detail", args=(obj.pk,))
        if hasattr(self, '_context'):
            if 'request' in self._context:
                request = self._context['request']
                return request.build_absolute_uri(uri)
        return build_absolute_uri(uri)  # skip-test-coverage


class ConcretePermissionSerializer(serializers.ModelSerializer):

    create_roles = serializers.StringRelatedField(many=True, read_only=True)
    update_roles = serializers.StringRelatedField(many=True, read_only=True)
    retrieve_roles = serializers.StringRelatedField(many=True, read_only=True)
    delete_roles = serializers.StringRelatedField(many=True, read_only=True)
    url = serializers.SerializerMethodField()

    def get_url(self, obj):
        uri = reverse("api_v1_1:acl-permission-detail", args=(obj.pk,))
        if hasattr(self, '_context'):
            if 'request' in self._context:
                request = self._context['request']
                return request.build_absolute_uri(uri)
        return build_absolute_uri(uri)  # skip-test-coverage

    create_roles_uid = serializers.PrimaryKeyRelatedField(
        source="create_roles",
        many=True,
        required=False,
        queryset=ConcreteRole.objects.all(),
    )
    update_roles_uid = serializers.PrimaryKeyRelatedField(
        source="update_roles",
        many=True,
        required=False,
        queryset=ConcreteRole.objects.all(),
    )
    retrieve_roles_uid = serializers.PrimaryKeyRelatedField(
        source="retrieve_roles",
        many=True,
        required=False,
        queryset=ConcreteRole.objects.all(),
    )
    delete_roles_uid = serializers.PrimaryKeyRelatedField(
        source="delete_roles",
        many=True,
        required=False,
        queryset=ConcreteRole.objects.all(),
    )

    class Meta:
        model = ConcretePermission
        fields = (
            "uid",
            "model_name",
            "create_roles",
            "update_roles",
            "retrieve_roles",
            "delete_roles",
            "create_roles_uid",
            "update_roles_uid",
            "retrieve_roles_uid",
            "delete_roles_uid",
            "url",
        )
        read_only_fields = (
            'uid',
            'users',
            "create_roles",
            "update_roles",
            "retrieve_roles",
            "delete_roles",
            'url',
            'created_by',
            'creation_date',
            'modification_date',
        )


class LDAPAuthLoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()


class TwoFactorLoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    token = serializers.CharField()
    verification_code = serializers.CharField()


class BlockedUserUpdateSerializer(serializers.Serializer):
    user_uids = serializers.ListField(child=serializers.UUIDField())
