# coding: utf-8
from __future__ import unicode_literals, absolute_import, print_function

AUTHORIZED_IP_PROTOCOLS = ("ipv4", "ipv6", "ipv4_6")
PROTOCOL_EQUIVALENCE = {"ipv4": "IPv4", "ipv6": "IPv6", "ipv4_6": "both"}

STD_MODEL_SPECIFIER_KEYS = (
    "std.specifier",
    "std.name",
    "std.verbose_name",
    # "std.verbose_name_plural",
    "std.description",
    "std.fields",
)

CONCRETE_COMMON_FIELDS = (
    'uid',
    'modification_date',
    'creation_date',
    'public',
)

CONCRETE_USER_PROTECTED_FIELDS = (
    'superuser',
    'level',
    'admin',
    'is_at_least_admin',
    'is_at_least_staff',
    'password_modification_date',
    'password_modification_token',
    'subscription_notification_token',
    'login_counter',
    'unsubscribe_to',
    'unsubscribe_all',
) + CONCRETE_COMMON_FIELDS

CONCRETE_MODELS_PROTECTED_FIELDS = (
    'created_by',
    'can_admin_users',
    'can_view_users',
    'can_admin_groups',
    'can_view_groups',
) + CONCRETE_COMMON_FIELDS

CONCRETE_CUSTOM_MODELS = (
    'TemporaryToken',
    'ConcreteRole',
    'ConcretePermission',
    'SecureConnectToken',
    'UserConfirmation',
    'ConfirmableUserAbstract',
    'HasPermissionAbstractUser',
    'PasswordChangeToken',
    'DefaultDivider',
    'DeletedModel',
)

STD_FIELD_SPECIFIER_KEYS = (
    "std.specifier",
    "std.name",
    "std.verbose_name",
    "std.description",
    "std.type",
)

STD_SPECIFIER = {
    "Model": STD_MODEL_SPECIFIER_KEYS,
    "Field": STD_FIELD_SPECIFIER_KEYS,
}

STD_MODEL_SPECIFIER_KEYS_V1 = ("fields", "name", "uid")
STD_FIELD_SPECIFIER_KEYS_V1 = ("datatype", "name", "attributes")

STD_SPECIFIER_V1 = {
    "Model": STD_MODEL_SPECIFIER_KEYS_V1,
    "Field": STD_FIELD_SPECIFIER_KEYS_V1,
}

TYPE_EQ_V1 = {
    'bool': 'BooleanField',
    'txt': 'TextField',
    'char': 'CharField',
    'url': 'URLField',
    'int': 'IntegerField',
    'bigint': 'BigIntegerField',
    'uid': 'UUIDField',
    'float': 'FloatField',
    'decimal': 'DecimalField',
    'json': 'JSONField',
    'file': 'FileField',
    'image': 'ImageField',
    'datetime': 'DateTimeField',
    'date': 'DateField',
    'email': 'EmailField',
    'fk': 'ForeignKey',
    'm2m': 'ManyToManyField',
    'ip': 'GenericIPAddressField',
    'point': 'PointField',
}


#:  Generic class attributes.
#:  When adding a new version, Class attributes should be added here
VERSIONS_ATTRIBUTES = {
    '1.0.0': {
        'field_type_spec': 'datatype',
        'fields_spec': 'fields',
        'element_name': 'name',
        'element_id': 'uid',
        'equivalence_table': TYPE_EQ_V1,
        'std_verifier': STD_SPECIFIER_V1,
    }
}
