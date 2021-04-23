# coding: utf-8
from collections import OrderedDict
from importlib import import_module

from django.contrib.auth import get_user_model
from django.conf import settings
from django.apps import apps

from rest_framework.reverse import reverse
from rest_framework import serializers
from drf_extra_fields.geo_fields import PointField

from concrete_datastore.concrete.models import LIST_USER_LEVEL
from concrete_datastore.concrete.models import (
    AuthToken,
    get_common_fields,
    get_user_tracked_fields,
    DIVIDER_MODEL,
    TemporaryToken,
)
from concrete_datastore.api.v1.validators import (
    validate_file,
    get_field_validator,
    is_field_required,
)
from concrete_datastore.concrete.meta import meta_registered
from concrete_datastore.concrete.meta import get_meta_definition_by_model_name
from concrete_datastore.api.v1 import DEFAULT_API_NAMESPACE
from concrete_datastore.api.v1.exceptions import (
    PasswordInsecureValidationError,
)
from concrete_datastore.api.v1.signals import build_absolute_uri


concrete = apps.get_app_config('concrete')


def default_session_control_exempt_rule(user):
    return False


def get_session_control_exempt_rule():
    module_name, func_name = settings.SESSION_CONTROL_DEFAULT_RULE.rsplit(
        '.', 1
    )
    module = import_module(module_name)
    session_control_exempt_rule = getattr(module, func_name)
    return session_control_exempt_rule


class AuthLoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()


class ChangePasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password1 = serializers.CharField()
    password2 = serializers.CharField()
    password_change_token = serializers.UUIDField(required=False)


class SecureLoginSerializer(serializers.Serializer):
    token = serializers.UUIDField()


class RegisterSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password1 = serializers.CharField(required=False, allow_null=True)
    password2 = serializers.CharField(required=False, allow_null=True)
    email_format = serializers.CharField(required=False, allow_null=True)
    url_format = serializers.CharField(
        required=False,
        allow_null=True,
        default=settings.DEFAULT_REGISTER_URL_FORMAT,
    )

    class Meta:
        fields = (
            "email",
            "password1",
            "password2",
            "email_format",
            "url_format",
        )

    def validate_url_format(self, value):
        if value is None:
            return settings.DEFAULT_REGISTER_URL_FORMAT
        return value


class ResetPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()
    url_format = serializers.CharField(
        required=False,
        allow_null=True,
        default=settings.DEFAULT_RESET_PASSWORD_URL_FORMAT,
    )

    class Meta:
        fields = ("email", "url_format")

    def validate_url_format(self, value):
        if value is None:
            return settings.DEFAULT_RESET_PASSWORD_URL_FORMAT
        return value


class UserSerializer(serializers.ModelSerializer):
    url = serializers.SerializerMethodField()
    token = serializers.SerializerMethodField()
    is_verified = serializers.SerializerMethodField()
    password = serializers.CharField(write_only=True, required=False)
    email = serializers.EmailField(required=True)
    level = serializers.CharField()
    groups = serializers.SerializerMethodField()

    api_namespace = DEFAULT_API_NAMESPACE

    def __init__(self, api_namespace, *args, **kwargs):
        self.api_namespace = api_namespace
        super(UserSerializer, self).__init__(*args, **kwargs)

    class Meta:
        model = get_user_model()
        fields = (
            "uid",
            'email',
            "url",
            "token",
            'first_name',
            "password",
            "last_name",
            "level",
            'is_verified',
            'groups',
            'external_auth',
            "{}s".format(DIVIDER_MODEL.lower()),
        )

    def get_groups(self, user):
        return user.concrete_groups.values_list('name', flat=True)

    def _get_token_key(self, user):
        if settings.USE_MULTIPLE_TOKENS is False:
            token = AuthToken.objects.filter(user=user, expired=False).first()
            if token:
                return token.key
        token = AuthToken.objects.create(user=user)
        return token.key

    def get_url(self, obj):
        uri = reverse("{}:account-me".format(self.api_namespace))
        return build_absolute_uri(uri)

    def get_is_verified(self, obj):
        module_name, func_name = settings.MFA_RULE_PER_USER.rsplit('.', 1)
        module = import_module(module_name)
        use_mfa_rule = getattr(module, func_name)
        if use_mfa_rule(user=obj) is False:
            return True

        return self.context.get('is_verified', False)

    def manage_session_token(self, obj):
        key = self._get_token_key(user=obj)

        rule = get_session_control_exempt_rule()
        user_is_session_control_exempted = rule(user=obj)

        session_control_enabled = settings.SESSIONS_NUMBER_CONTROL_ENABLED
        max_sessions_allowed = settings.MAX_SIMULTANEOUS_SESSIONS
        unlimited_sessions = settings.MAX_SIMULTANEOUS_SESSIONS == 0
        user_active_tokens = (
            AuthToken.objects.filter(user=obj, expired=False)
            .exclude(key=key)
            .order_by('expiration_date')
        )
        if (
            session_control_enabled
            and user_active_tokens.count() >= max_sessions_allowed
            and not unlimited_sessions
            and not user_is_session_control_exempted
        ):
            # On va expirer les tokens les plus anciens tant que le nombre
            # total de token actifs est >= MAX_SIMULTANEOUS_SESSIONS
            # NB: le token nouvellement créé ne fait pas partie de ce queryset
            # d'où le +1
            tokens_count = user_active_tokens.count()
            nb_of_token_to_expire = tokens_count - max_sessions_allowed + 1
            tokens_to_expire_pks = user_active_tokens.values_list(
                'pk', flat=True
            )[:nb_of_token_to_expire]
            AuthToken.objects.filter(pk__in=tokens_to_expire_pks).update(
                expired=True
            )

        return key

    def get_token(self, obj):
        #: If the user has not the minimum level for two factor
        #: Return the final token
        module_name, func_name = settings.MFA_RULE_PER_USER.rsplit('.', 1)
        module = import_module(module_name)
        use_mfa_rule = getattr(module, func_name)
        if use_mfa_rule(user=obj):
            #: With two factor auth enable
            #: return the token if identity has been validated
            is_verified = self.context.get('is_verified', False)
            if is_verified:
                token_key = self.manage_session_token(obj)
            else:
                token = TemporaryToken.objects.create(user=obj)
                token_key = token.key

        else:
            token_key = self.manage_session_token(obj)
        return token_key


def make_related_serializer_class(
    target_model_name, many, nested=False, api_namespace=DEFAULT_API_NAMESPACE
):

    if target_model_name not in meta_registered:
        raise ValueError(f'Related to unknown model {target_model_name}')

    rel_meta_model = meta_registered[target_model_name]
    rel_serializer_class = make_serializer_class(
        meta_model=rel_meta_model, nested=nested, api_namespace=api_namespace
    )

    return rel_serializer_class(many=many)


def make_custom_serializer_fields(
    meta_model, api_namespace=DEFAULT_API_NAMESPACE
):
    custom_fields_attrs = {}

    CONCRETE_SETTINGS = getattr(settings, 'CONCRETE', {})
    SERIALIZERS_SETTINGS = CONCRETE_SETTINGS.get('SERIALIZERS', {})

    for model_name, SERIALIZER_SETTINGS in SERIALIZERS_SETTINGS.items():
        if meta_model.get_model_name() == model_name:

            CUSTOM_FIELDS = SERIALIZER_SETTINGS.get('CUSTOM_FIELDS', {})

            for field_name, field_args in CUSTOM_FIELDS.items():

                if 'type' not in field_args:
                    raise ValueError(
                        'CONCRETE improperly configured : custom field '
                        f'{field_name} should have a type attribute'
                    )

                if field_args['type'] == 'RelatedModelSerializer':

                    if 'to' not in field_args:
                        raise ValueError(
                            'CONCRETE improperly configured : custom field '
                            f'{field_name} with type RelatedModelSerializer '
                            'should have a "to" argument'
                        )

                    custom_fields_attrs.update(
                        {
                            field_name: make_related_serializer_class(
                                target_model_name=field_args['to'],
                                many=True,
                                nested=False,
                                api_namespace=api_namespace,
                            )
                        }
                    )
                else:
                    raise NotImplementedError(
                        'Generic type for custom field in serializer is '
                        'not implemented in this version of concrete'
                    )

    return custom_fields_attrs.keys(), custom_fields_attrs


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
        extra_kwargs = {
            name: {'required': is_field_required(field)}
            for name, field in enum_fields
        }

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
                        required=False,
                        allow_null=True,
                        validators=[validate_file],
                    )
                }
            )
        if field.f_type == 'PointField':
            attrs.update(
                {
                    name: PointField(
                        required=not field.f_args.get("blank", False),
                        allow_null=True,
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
        attrs.update({f'validate_{name}': get_field_validator(field=field)})
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

    return type(
        str('AccountMeSerializer'),
        (meta_serializer_class,),
        {
            'Meta': Meta,
            'level': serializers.SerializerMethodField(),
            'get_level': lambda self, obj: obj.get_level(),
        },
    )


class ConcretePasswordValidator(object):
    def __call__(self, value):
        try:
            for validator in settings.AUTH_PASSWORD_VALIDATORS:
                module_name, validator_name = validator['NAME'].rsplit('.', 1)
                module = import_module(module_name)
                validator_cls = getattr(module, validator_name)
                validator_cls().validate(value)
        except PasswordInsecureValidationError:
            raise
        except Exception as e:
            raise PasswordInsecureValidationError(
                str(e), code='PASSWORD_INSECURE'
            )
