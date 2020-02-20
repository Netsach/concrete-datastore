# coding: utf-8
from collections import OrderedDict

from django.apps import apps
from django.conf import settings
from django.contrib.auth import get_user_model

from rest_framework.reverse import reverse
from rest_framework import serializers

from concrete_datastore.concrete.models import (
    get_common_fields,
    get_user_tracked_fields,
    DIVIDER_MODEL,
    ConcreteRole,
    ConcretePermission,
    EmailDevice,
)
from concrete_datastore.api.v1 import DEFAULT_API_NAMESPACE
from concrete_datastore.api.v1.serializers import (
    make_custom_serializer_fields,
    make_related_serializer_class,
)
from concrete_datastore.api.v1.validators import validate_file
from concrete_datastore.concrete.models import LIST_USER_LEVEL
from concrete_datastore.api.v1.signals import build_absolute_uri
from concrete_datastore.concrete.meta import get_meta_definition_by_model_name

concrete = apps.get_app_config('concrete')


def make_serializer_class(
    meta_model,
    api_namespace=DEFAULT_API_NAMESPACE,
    limit_fields=None,
    nested=True,
    safe=False,
):
    enum_fields = list(meta_model.get_fields())
    dict_fields = OrderedDict(enum_fields)
    _all_fields = (
        list(dict_fields.keys())
        + list(get_common_fields().keys())
        + ['url', 'verbose_name']
    )

    custom_fields_names, custom_fields_attrs = make_custom_serializer_fields(
        meta_model, api_namespace=api_namespace
    )

    _all_fields += custom_fields_names
    if meta_model.get_model_name() not in ('User',):
        _all_fields += get_user_tracked_fields().keys()
    if meta_model.get_model_name() not in ('User', DIVIDER_MODEL):
        _all_fields += ['scopes']
    api_display_fields = meta_model.get_property('m_api_list_display') or []
    if api_display_fields == []:
        if limit_fields is None:
            _fields = _all_fields
        else:
            _fields = [f for f in _all_fields if f in limit_fields]
    else:
        _fields = api_display_fields
    if meta_model.get_model_name() == 'User' and api_display_fields == []:
        _fields += [
            'last_name',
            'first_name',
            "{}s".format(DIVIDER_MODEL.lower()),
            "admin",
            "is_staff",
            "level",
            "unsubscribe_notification_url",
            "unsubscribe_all",
            "unsubscribe_to",
            "external_auth",
        ]

        if safe:
            _fields += ['email']

    # TODO: rajouter les <name>_uid dans _fields
    fk_read_only_fields = []
    for name, field in enum_fields:
        if field.type.startswith("rel_"):
            _fields += ['{}_uid'.format(name)]
            fk_read_only_fields += [name]

    class Meta:
        model = concrete.models[meta_model.get_model_name().lower()]
        fields = _fields

        read_only_fields = (
            ['created_by', 'admin', 'is_staff']
            + fk_read_only_fields
            + [f for f in _all_fields if f.startswith('resource_')]
        )
        extra_kwargs = {}
        for name, field in enum_fields:
            if field.f_args.get('blank', False) is False:
                extra_kwargs[name] = {'required': True}

        # TODO: DEACTIVATED by LCO on 06/11/18
        # vars_model = vars(model)
        # for key, value in vars_model.items():
        #     # TODO: Exclude model User
        #     if isinstance(value, ReverseManyToOneDescriptor):
        #         if not (key.startswith('divider') or (key.startswith('can'))):
        #             fields.append(key)
        #             read_only_fields.append(key)

    attrs = {'Meta': Meta}

    # TODO : if field is relational, expose pk and url serialized
    for name, field in enum_fields:
        if field.f_type == 'FileField':
            attrs.update(
                {
                    name: serializers.FileField(
                        required=False, validators=[validate_file]
                    )
                }
            )
        if field.f_type == 'JSONField':
            attrs.update(
                {name: serializers.JSONField(binary=False, required=False)}
            )
        if field.type.startswith("rel_") and nested is True:

            force_nested = getattr(field, 'force_nested', False)

            attrs.update(
                {
                    name: make_related_serializer_class(
                        target_model_name=field.f_args['to'],
                        many=(field.type == 'rel_iterable'),
                        nested=force_nested,
                        api_namespace=api_namespace,
                    )
                }
            )

    attrs.update(custom_fields_attrs)

    class _ModelSerializer(serializers.ModelSerializer):
        url = serializers.SerializerMethodField()
        verbose_name = serializers.SerializerMethodField()
        scopes = serializers.SerializerMethodField()

        def get_scopes(self, obj):
            user = self.context.get('request').user
            superuser = user.is_superuser is True
            at_least_admin = (
                False if user.is_anonymous else user.is_at_least_admin
            )
            staff = False if user.is_anonymous else user.is_at_least_staff

            if staff or at_least_admin or superuser:
                divider = getattr(obj, DIVIDER_MODEL.lower(), None)
                if divider:
                    return {"entity_uid": divider.uid}
            return None

        def get_url(self, obj):
            uri = reverse(
                "{}:{}-detail".format(
                    api_namespace, meta_model.get_dashed_case_class_name()
                ),
                args=(obj.pk,),
            )
            if hasattr(self, '_context'):
                if 'request' in self._context:
                    request = self._context['request']
                    return request.build_absolute_uri(uri)
            return build_absolute_uri(uri)  # skip-test-coverage

        def get_verbose_name(self, obj):
            try:
                return str(obj)
            except Exception:
                return ''

    for name, field in enum_fields:
        if field.type.startswith("rel_i"):
            x = field.f_args["to"].split('.')
            field_model = apps.get_model(app_label=x[0], model_name=x[1])
            required = not field.f_args.get("blank", False)
            attrs.update(
                {
                    '{}_uid'.format(name): serializers.PrimaryKeyRelatedField(
                        source=name,
                        many=True,
                        allow_null=True,
                        required=required,
                        queryset=field_model.objects.all(),
                    )
                }
            )

        if field.type.startswith("rel_s"):
            # Ex: concrete.Category, split to get
            # Django model with apps.get_model()
            x = field.f_args["to"].split('.')
            field_model = apps.get_model(app_label=x[0], model_name=x[1])
            required = not field.f_args.get("blank", False)
            null = field.f_args.get("null", False)
            attrs.update(
                {
                    '{}_uid'.format(name): serializers.PrimaryKeyRelatedField(
                        many=False,
                        source=name,
                        allow_null=null,
                        required=required,
                        queryset=field_model.objects.all(),
                    )
                }
            )

    if meta_model.get_model_name() == 'User':
        attrs.update({'level': serializers.CharField()})

        def validate_level(self, value):
            value = value.lower()

            if value not in LIST_USER_LEVEL:
                raise serializers.ValidationError("Wrong value")

            else:
                user_level = self.context.get('request').user.level
                forbidden_for_admin = user_level == "admin" and value in [
                    "admin",
                    "superuser",
                ]
                forbidden_for_manager = user_level == "manager" and value in [
                    "admin",
                    "superuser",
                    "manager",
                    "blocked",
                ]
                forbidden_for_simple = user_level == "simpleuser"
                if (
                    forbidden_for_manager
                    or forbidden_for_admin
                    or forbidden_for_simple
                ):
                    raise serializers.ValidationError(
                        "You don't have permission to set this level"
                    )
            return value

        _ModelSerializer.validate_level = validate_level

        attrs.update(
            {
                'unsubscribe_notification_url': serializers.SerializerMethodField(
                    'get_unsubscribe_url'
                )
            }
        )

        def get_unsubscribe_url(self, obj):
            return '{scheme}://{domain}:{port}{uri}'.format(
                scheme=settings.SCHEME,
                domain=settings.HOSTNAME,
                port=settings.PORT,
                uri=reverse(
                    'concrete:unsubscribe_notifications',
                    kwargs={'token': obj.subscription_notification_token},
                ),
            )

        _ModelSerializer.get_unsubscribe_url = get_unsubscribe_url

    api_model_serializer = type(
        str('{}ModelSerializer'.format(meta_model.get_model_name())),
        (_ModelSerializer,),
        attrs,
    )
    return api_model_serializer


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
