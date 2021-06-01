# coding: utf-8
import pendulum
import binascii
import logging
import uuid
import sys
import os

from collections import defaultdict
from itertools import chain
from binascii import unhexlify
from datetime import date

from django.contrib.postgres.fields import JSONField
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils.translation import ugettext_lazy as _
from django.core.exceptions import ObjectDoesNotExist
from django.utils.encoding import force_text
from django_otp.models import Device
from django_otp.oath import totp
from django_otp.util import hex_validator, random_hex
from django.utils import timezone
from django.conf import settings
from django.urls import reverse
from django.apps import apps
from django.contrib.gis.db import models  # it includes all default fields

from rest_framework.authtoken.models import Token

from concrete_datastore.concrete.meta import (
    get_meta_definition_by_model_name,
    meta_models,
    make_unicode_method,
)
from concrete_datastore.api.v1.validators import validate_file
from concrete_datastore.concrete.constants import (
    ATLEAST_LEVEL_ATTRS,
    EXACT_LEVEL_ATTRS,
    CRUD_LEVEL,
    LIST_USER_LEVEL,
    HANDELED_MODELISATION_VERSIONS,
    TYPE_EQ,
)

# Since a lot of models are meta-declared, deactivate pylint no-member here
# pylint: disable=no-member


def get_fields_and_types_of_model(model):
    fields_and_types = defaultdict(lambda: 'Unknow type')
    meta_model = get_meta_definition_by_model_name(model.__name__)
    for field_name, field in meta_model.get_fields():
        fields_and_types[field_name] = TYPE_EQ.get(field.f_type, 'Unknow type')
    return fields_and_types


def compute_auth_token_expiry():
    now = pendulum.now('utc')
    if settings.API_TOKEN_EXPIRY == 0:
        return now.add(years=100)
    return now.add(minutes=settings.API_TOKEN_EXPIRY)


def compute_pwd_change_token_expiry():
    now = pendulum.now('utc')
    return now.add(hours=settings.PASSWORD_CHANGE_TOKEN_EXPIRY_HOURS)


class AuthToken(Token):
    user = models.ForeignKey(
        'concrete.User',
        related_name='auth_tokens',
        on_delete=models.CASCADE,
        verbose_name=_("User"),
    )
    expired = models.BooleanField(default=False)
    expiration_date = models.DateTimeField(default=compute_auth_token_expiry)
    last_action_date = models.DateTimeField(default=timezone.now)


def default_key():
    return force_text(random_hex(20))


def key_validator(value):
    return hex_validator()(value)


class EmailDevice(Device):
    """
    A :class:`~django_otp.models.Device` that delivers a token to the user's
    registered email address (``user.email``). This is intended for
    demonstration purposes; if you allow users to reset their passwords via
    email, then this provides no security benefits.

    .. attribute:: key

        *CharField*: A hex-encoded secret key of up to 40 bytes. (Default: 20
        random bytes)
    """

    uid = models.UUIDField(default=uuid.uuid4, primary_key=True)
    key = models.CharField(
        max_length=80,
        validators=[key_validator],
        default=default_key,
        help_text='A hex-encoded secret key of up to 20 bytes.',
    )
    email = models.CharField(
        max_length=250,
        default='',
        help_text='Email address to send verification code.',
    )
    modification_date = models.DateTimeField(auto_now=True)
    creation_date = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        'concrete.User',
        related_name="owned_%(class)ss",
        null=True,
        on_delete=models.PROTECT,
    )

    @property
    def id(self):
        return self.pk

    @property
    def bin_key(self):
        return unhexlify(self.key.encode())

    def generate_challenge(self):
        code_timeout = settings.TWO_FACTOR_CODE_TIMEOUT_SECONDS
        token = totp(self.bin_key, step=code_timeout)

        main_app = apps.get_app_config('concrete')
        body = settings.TWO_FACTOR_TOKEN_MSG.format(
            platform_name=settings.PLATFORM_NAME,
            confirm_code=token,
            min_validity=int(code_timeout / 60),
        )
        main_app.models['email'].objects.create(
            receiver=self.user,
            body=body,
            resource_status='to-send',
            subject='[Confirmation authentication {}]'.format(
                settings.PLATFORM_NAME
            ),
            created_by=self.user,
        )
        logging.debug(
            'Confirm Email has been sent to {}'.format(self.user.email)
        )

        return token

    def verify_token(self, token):
        try:
            token = int(token)
        except Exception:
            verified = False
        else:
            verified = any(
                totp(
                    self.bin_key,
                    step=settings.TWO_FACTOR_CODE_TIMEOUT_SECONDS,
                    drift=drift,
                )
                == token
                for drift in [0, -1]
            )

        return verified

    @classmethod
    def from_persistent_id(cls, persistent_id):
        """
        Loads a device from its persistent id::

            device == Device.from_persistent_id(device.persistent_id)

        """
        device = None

        try:
            model_label, device_id = persistent_id.rsplit('/', 1)
            app_label, model_name = model_label.split('.')

            main_app = apps.get_app_config(app_label)

            device_cls = main_app.models[model_name]
            if issubclass(device_cls, Device):
                device = device_cls.objects.filter(pk=device_id).first()
        except (ValueError, LookupError):
            pass

        return device


class TemporaryToken(models.Model):
    """
    The temporary authorization token model for two factor auth
    """

    key = models.CharField(_("Key"), max_length=40, primary_key=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='temporary_tokens',
        on_delete=models.CASCADE,
        verbose_name=_("User"),
    )
    expired = models.BooleanField(default=False)
    creation_date = models.DateTimeField(auto_now_add=True)
    modification_date = models.DateTimeField(auto_now=True)
    ordering = ('-modification_date', '-creation_date')

    class Meta:
        verbose_name = _("Temporary Token")
        verbose_name_plural = _("Temporary Tokens")

    def save(self, *args, **kwargs):
        if not self.key:
            self.key = self.generate_key()
        return super().save(*args, **kwargs)

    def generate_key(self):
        return binascii.hexlify(os.urandom(20)).decode()

    def __str__(self):
        return self.key


class ConcreteRole(models.Model):
    class Meta:
        verbose_name = 'Role'

    uid = models.UUIDField(default=uuid.uuid4, primary_key=True)
    name = models.CharField(
        unique=True, blank=False, null=False, max_length=255
    )
    users = models.ManyToManyField(
        'concrete.User', blank=True, related_name='concrete_roles'
    )
    created_by = models.ForeignKey(
        'concrete.User',
        related_name="owned_%(class)ss",
        null=True,
        on_delete=models.PROTECT,
    )
    modification_date = models.DateTimeField(
        auto_now=True,
        # default=timezone.now
    )
    creation_date = models.DateTimeField(
        auto_now_add=True,
        # default=timezone.now
    )

    def __str__(self):
        # the __str__ method should return a string
        return str(self.name)


class ConcretePermission(models.Model):
    class Meta:
        verbose_name = 'Permission'

    uid = models.UUIDField(default=uuid.uuid4, primary_key=True)
    model_name = models.CharField(
        unique=True, blank=False, null=False, max_length=255
    )

    create_roles = models.ManyToManyField(
        ConcreteRole, blank=True, related_name='create_permissions'
    )
    retrieve_roles = models.ManyToManyField(
        ConcreteRole, blank=True, related_name='retrieve_permissions'
    )
    update_roles = models.ManyToManyField(
        ConcreteRole, blank=True, related_name='update_permissions'
    )
    delete_roles = models.ManyToManyField(
        ConcreteRole, blank=True, related_name='delete_permissions'
    )
    created_by = models.ForeignKey(
        'concrete.User',
        related_name="owned_%(class)ss",
        null=True,
        on_delete=models.PROTECT,
    )

    modification_date = models.DateTimeField(auto_now=True)
    creation_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        # the __str__ method should return a string
        return str(self.model_name)


class SecureConnectToken(models.Model):
    value = models.UUIDField(default=uuid.uuid4, primary_key=True)
    user = models.ForeignKey(
        'concrete.User',
        on_delete=models.PROTECT,
        related_name='secure_connect_tokens',
    )
    creation_date = models.DateTimeField(auto_now_add=True)
    modification_date = models.DateTimeField(auto_now=True)
    expired = models.BooleanField(default=False)

    mail_sent = models.BooleanField(default=False)
    url = models.URLField(blank=True, null=True)

    def __str__(self):
        return str(self.value)

    def send_mail(self):
        main_app = apps.get_app_config('concrete')
        body = settings.SECURE_TOKEN_MESSAGE_BODY.format(
            platform=settings.PLATFORM_NAME,
            email=self.user.email,
            link=self.url,
        )

        main_app.models['email'].objects.create(
            receiver=self.user,
            body=body,
            resource_status='to-send',
            subject='[Authentication {}]'.format(settings.PLATFORM_NAME),
            created_by=self.user,
        )
        logging.debug(
            'Confirm Email has been sent to {}'.format(self.user.email)
        )
        self.mail_sent = True
        self.save()


class UserConfirmation(models.Model):
    uid = models.UUIDField(default=uuid.uuid4, primary_key=True)
    confirmed = models.BooleanField(default=False)
    user = models.ForeignKey(
        'concrete.User', on_delete=models.CASCADE, related_name='confirmations'
    )
    creation_date = models.DateTimeField(auto_now_add=True)
    modification_date = models.DateTimeField(auto_now=True)
    redirect_to = models.URLField(null=True)
    link_sent = models.BooleanField(default=False)

    @property
    def url(self):
        return '{scheme}://{domain}:{port}{uri}'.format(
            scheme=settings.SCHEME,
            domain=settings.HOSTNAME,
            port=settings.PORT,
            uri=reverse(
                'concrete:email_confirmation', kwargs={'token': self.uid}
            ),
        )

    def send_link(self, body=None):
        main_app = apps.get_app_config('concrete')
        if body is None:
            body = settings.AUTH_CONFIRM_EMAIL_MESSAGE_BODY.format(
                platform=settings.PLATFORM_NAME,
                email=self.user.email,
                link=self.url,
            )
        main_app.models['email'].objects.create(
            receiver=self.user,
            body=body,
            resource_status='to-send',
            subject='Confirmation mail',
            created_by=self.user,
        )
        logging.debug(
            'Confirm Email has been sent to {}'.format(self.user.email)
        )
        self.link_sent = True
        self.save()


class ConfirmableUserAbstract(models.Model):
    class Meta:
        abstract = True

    def is_confirmed(self):
        if settings.AUTH_CONFIRM_EMAIL_ENABLE is False:
            return True
        confirmation = self.confirmations
        try:
            return confirmation.latest('modification_date').confirmed
        except ObjectDoesNotExist:
            return False

    def get_or_create_confirmation(self, redirect_to=None):
        if redirect_to is None:
            redirect_to = settings.AUTH_CONFIRM_EMAIL_DEFAULT_REDIRECT_TO
        try:
            return self.confirmations.latest('modification_date')
        except ObjectDoesNotExist:
            return self.confirmations.create(redirect_to=redirect_to)

    def confirmate(self):
        self.confirmations.all().update(confirmed=True)


class HasPermissionAbstractUser(models.Model):
    _is_verified = False

    def is_verified(self):
        return self._is_verified

    class Meta:
        abstract = True

    def __setattr__(self, attrname, val):
        if attrname == 'level':
            kwargs = {'level': val, 'commit': True}
            getattr(self, 'set_level')(**kwargs)
        else:
            super(HasPermissionAbstractUser, self).__setattr__(attrname, val)

    @property
    def is_at_least_admin(self):
        return self.admin is True or self.is_superuser is True

    @property
    def is_at_least_staff(self):
        return self.is_staff is True or self.is_at_least_admin is True

    def set_level(self, level, commit=False):
        list_levels = LIST_USER_LEVEL

        if type(level) != str:
            level = str(level)

        level = level.lower()

        if level in list_levels:
            self.is_superuser = level in ('superuser',)
            self.admin = level in ('admin', 'superuser')
            self.is_staff = level in ('superuser', 'admin', 'manager')
            self.is_active = level != 'blocked'

        if commit is True:
            self.save()

    def get_level(self):
        if self.is_active is False:
            return 'Blocked'
        elif self.is_superuser:
            return 'SuperUser'
        elif self.admin:
            return 'Admin'
        elif self.is_staff:
            return 'Manager'
        return 'SimpleUser'

    def get_roles(self):
        roles = self.concrete_roles.values_list('name', flat=True)
        return roles

    def get_roles_uid(self):
        roles = self.concrete_roles.values_list('uid', flat=True)
        return roles

    @property
    def id(self):
        return self.pk

    @property
    def level(self):
        if self.is_superuser:
            return 'superuser'
        elif self.admin:
            return 'admin'
        elif self.is_staff:
            return 'manager'
        elif self.is_active:
            return 'simpleuser'
        else:
            return 'blocked'

    @classmethod
    def filter_by_at_least_level(cls, level, queryset=None):
        queryset = queryset or cls.objects.all()
        if level == 'blocked' or level not in ATLEAST_LEVEL_ATTRS.keys():
            # A user cannot be at least blocked
            return queryset.none()
        return queryset.filter(**ATLEAST_LEVEL_ATTRS[level])

    @classmethod
    def filter_by_exact_level(cls, level, queryset=None):
        queryset = queryset or cls.objects.all()
        if level not in EXACT_LEVEL_ATTRS.keys():
            return queryset.none()
        return queryset.filter(**EXACT_LEVEL_ATTRS[level])

    def __gt__(self, other):
        if isinstance(other, self.__class__) is False:
            raise ValueError(
                "The element to compare with should be an instance of User"
            )
        if LIST_USER_LEVEL.index(self.level) > LIST_USER_LEVEL.index(
            other.level
        ):
            return True
        return False

    def __ge__(self, other):
        if isinstance(other, self.__class__) is False:
            raise ValueError(
                "The element to compare with should be an instance of User"
            )
        if LIST_USER_LEVEL.index(self.level) >= LIST_USER_LEVEL.index(
            other.level
        ):
            return True
        return False

    def __lt__(self, user):
        if isinstance(user, self.__class__) is False:
            raise ValueError(
                "The element to compare with should be an instance of User"
            )
        if LIST_USER_LEVEL.index(self.level) < LIST_USER_LEVEL.index(
            user.level
        ):
            return True
        return False

    def __le__(self, user):
        if isinstance(user, self.__class__) is False:
            raise ValueError(
                "The element to compare with should be an instance of User"
            )
        if LIST_USER_LEVEL.index(self.level) <= LIST_USER_LEVEL.index(
            user.level
        ):
            return True
        return False

    @property
    def password_has_expired(self):
        expiry = settings.PASSWORD_EXPIRY_TIME
        password_has_expiry = expiry > 0
        now = pendulum.now()
        d = self.password_modification_date
        last_password_modification = pendulum.datetime(d.year, d.month, d.day)

        return (
            password_has_expiry
            and now.diff(last_password_modification).in_days() >= expiry
        )


class PasswordChangeToken(models.Model):

    uid = models.UUIDField(primary_key=True, default=uuid.uuid4)
    creation_date = models.DateTimeField(auto_now_add=True)
    expiry_date = models.DateTimeField(default=compute_pwd_change_token_expiry)
    user = models.ForeignKey(
        'concrete.User',
        related_name="reset_password_tokens",
        on_delete=models.PROTECT,
    )


class DefaultDivider(models.Model):
    uid = models.UUIDField(primary_key=True, default=uuid.uuid4)
    name = models.CharField(max_length=250, default="Default Divider")


class DeletedModel(models.Model):
    uid = models.UUIDField()

    model_name = models.CharField(max_length=255, default='')

    modification_date = models.DateTimeField(auto_now=True)

    creation_date = models.DateTimeField(auto_now_add=True)


class UserManager(BaseUserManager):
    """Define a model manager for User model with no username field."""

    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        """Create and save a User with the given email and password."""
        if not email:
            raise ValueError('The given email must be set')
        email = self.normalize_email(email).lower()
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        """Create and save a regular User with the given email and password."""
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password, **extra_fields):
        """Create and save a SuperUser with the given email and password."""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self._create_user(email, password, **extra_fields)


def get_common_fields(public_default_value=False):
    if public_default_value not in (True, False):
        raise ValueError(
            "Value of 'public_default_value' should be whether True or False"
        )
    return {
        'uid': models.UUIDField(primary_key=True, default=uuid.uuid4),
        'modification_date': models.DateTimeField(
            auto_now=True,
            # default=timezone.now
        ),
        'creation_date': models.DateTimeField(
            auto_now_add=True,
            # default=timezone.now
        ),
        'public': models.BooleanField(default=public_default_value),
    }


def get_user_tracked_fields():
    return {
        'created_by': models.ForeignKey(
            'concrete.User',
            related_name="owned_%(class)ss",
            null=True,
            on_delete=models.PROTECT,
        ),
        'can_admin_users': models.ManyToManyField(
            'concrete.User',
            related_name="administrable_%(class)ss",
            blank=True,
        ),
        'can_view_users': models.ManyToManyField(
            'concrete.User', related_name="viewable_%(class)ss", blank=True
        ),
        'can_admin_groups': models.ManyToManyField(
            'concrete.Group',
            related_name="group_administrable_%(class)ss",
            blank=True,
        ),
        'can_view_groups': models.ManyToManyField(
            'concrete.Group',
            related_name="group_viewable_%(class)ss",
            blank=True,
        ),
    }


def get_divider_fields_foreignkey(model):
    return {
        '{}'.format(DIVIDER_MODEL.lower()): models.ForeignKey(
            'concrete.{}'.format(model),
            related_name="divider_%(class)ss",
            null=True,
            blank=True,
            on_delete=models.PROTECT,
        ),
        "additional_filtering": models.BooleanField(default=False),
    }


def get_divider_fields_manytomany(model):
    return {
        '{}s'.format(DIVIDER_MODEL.lower()): models.ManyToManyField(
            'concrete.{}'.format(model),
            related_name="divider_%(class)ss",
            blank=True,
        )
    }


def get_divider_notification_fields(model):
    return {
        'unsubscribe_all': models.BooleanField(default=False),
        'unsubscribe_to': models.ManyToManyField(
            'concrete.{}'.format(model),
            related_name="unsubscribed_%(class)ss",
            blank=True,
        ),
    }


def get_minimum_level(meta_model, prop_name, default_value):
    level = meta_model.get_property(
        prop_name=prop_name, default_value=default_value
    )
    if level not in CRUD_LEVEL:
        return default_value
    return level


def make_django_model(meta_model, divider):
    class Meta:
        verbose_name = _(meta_model.get_verbose_name())
        verbose_name_plural = _(meta_model.get_verbose_name_plural())
        ordering = ('-modification_date', '-creation_date')
        unique_together = tuple(
            meta_model.get_property(
                prop_name='m_unique_together', default_value=[]
            )
        )

    modelisation_version = getattr(meta_model, 'version', None)

    if (
        modelisation_version is not None
        and modelisation_version not in HANDELED_MODELISATION_VERSIONS
    ):
        raise ValueError('Unknown modelisation format')

    creation_level = get_minimum_level(
        meta_model=meta_model,
        prop_name='m_creation_minimum_level',
        default_value='authenticated',
    )

    retrieve_level = get_minimum_level(
        meta_model=meta_model,
        prop_name='m_retrieve_minimum_level',
        default_value='authenticated',
    )

    update_level = get_minimum_level(
        meta_model=meta_model,
        prop_name='m_update_minimum_level',
        default_value='authenticated',
    )

    delete_level = get_minimum_level(
        meta_model=meta_model,
        prop_name='m_delete_minimum_level',
        default_value='superuser',
    )

    attrs = {
        'Meta': Meta,
        '__module__': 'concrete_datastore.concrete.models',
        '__str__': make_unicode_method(meta_model),
        '__creation_minimum_level__': creation_level,
        '__retrieve_minimum_level__': retrieve_level,
        '__update_minimum_level__': update_level,
        '__delete_minimum_level__': delete_level,
    }

    is_default_public = meta_model.get_property(
        prop_name='m_is_default_public', default_value=False
    )
    if is_default_public is None or is_default_public not in (True, False):
        is_default_public = False
    attrs.update(get_common_fields(public_default_value=is_default_public))

    ancestors = (models.Model,)
    if meta_model.get_model_name() == 'User':
        ancestors = (
            AbstractUser,
            HasPermissionAbstractUser,
            ConfirmableUserAbstract,
        )
        attrs.update(
            {
                'username': None,
                'objects': UserManager(),
                'admin': models.BooleanField(default=False),
                'password_modification_date': models.DateField(
                    default=date.today
                ),
                'subscription_notification_token': models.UUIDField(
                    default=uuid.uuid4, editable=False
                ),
                'login_counter': models.IntegerField(default=0),
                'external_auth': models.BooleanField(default=False),
                # True if user created by an external auth
                'USERNAME_FIELD': 'email',
                'REQUIRED_FIELDS': [],
            }
        )
    else:
        attrs.update(get_user_tracked_fields())

    for field_name, field in meta_model.get_fields():
        if field_name in attrs:
            raise ValueError(
                f'{field_name} is a protected field and cannot be overwritten'
            )

        # obsoletes fields
        if meta_model.get_model_name() == 'User':
            obsoletes_level = ('guest', 'manager', 'blocked')
            if field_name in obsoletes_level:
                raise ValueError(
                    f'The fields {obsoletes_level} are no longer supported'
                )

        args = field.f_args
        if field.f_type == 'FileField':
            args.update(
                {'blank': True, 'null': True, 'validators': [validate_file]}
            )
        elif field.f_type == 'JSONField':
            json_args = args
            json_args['blank'] = True
            json_args['encoder'] = None
            json_args['null'] = False
            json_args['default'] = dict
            attrs.update({field_name: JSONField(**json_args)})
            continue
        elif field.f_type in ('CharField', 'TextField'):
            args['null'] = False
            args.setdefault('blank', True)
            args.setdefault('default', "")
        elif field.f_type in ('IntegerField', 'BigIntegerField'):
            args['null'] = False
            args.setdefault('blank', True)
            args.setdefault('default', 0)
        elif field.f_type == 'DecimalField':
            args['null'] = False
            args.setdefault('decimal_places', 2)
            args.setdefault('max_digits', 20)
            args.setdefault('default', 0.00)
        elif field.f_type in ('ForeignKey',):

            # Copy args to not alter the real field.f_args
            args = args.copy()
            # Force FK to null=True to avoid default value problems
            args.update({'null': True})
            # PROTECT foreign key deletion by default
            on_delete_rule = args.get('on_delete', 'PROTECT')
            if on_delete_rule not in ('CASCADE', 'SET_NULL', 'PROTECT'):
                raise ValueError(
                    f'On delete rule "{on_delete_rule}" is invalid. '
                    'It must be "CASCADE", "SET_NULL" or "PROTECT"'
                )

            args.update({'on_delete': getattr(models, on_delete_rule)})

        elif field.f_type in ('GenericIPAddressField',):
            #: If blank is True, null should be too
            #: https://docs.djangoproject.com/fr/3.1/ref/models/fields/#genericipaddressfield
            if args.get('blank', False) is True:
                args['null'] = True
            else:
                args.setdefault('blank', False)
                args['null'] = False

        elif field.f_type in ('DateTimeField',):
            if args.get('null', False) is True:
                args['null'] = True
                args['blank'] = True
            else:
                args['default'] = timezone.now
                args['null'] = False
                args.setdefault('blank', False)
        elif field.f_type in ('DateField',):
            if args.get('null', False) is True:
                args['null'] = True
                args['blank'] = True
            else:
                args['default'] = date.today
                args['null'] = False
                args.setdefault('blank', False)
        elif field.f_type == 'ManyToManyField':
            # Copy args to not alter the real field.f_args
            args = args.copy()
            args.pop('null', None)
        attrs.update({field_name: getattr(models, field.f_type)(**args)})
    if meta_model.get_model_name() != divider:
        if meta_model.get_model_name() == "User":
            attrs.update(get_divider_fields_manytomany(divider))
            attrs.update(get_divider_notification_fields(divider))
            attrs.update(
                {'email': models.EmailField(_('email address'), unique=True)}
            )
        elif meta_model.get_model_name() in UNDIVIDED_MODEL:
            pass
        else:
            attrs.update(get_divider_fields_foreignkey(divider))

    return type(meta_model.get_model_name(), ancestors, attrs)


def get_divider_v0(meta_model):
    if meta_model.get_model_name() == "EntityDividerModel":
        try:
            return meta_model.get_property(prop_name="fields")[0].name
        except IndexError:
            return 'DefaultDivider'


def get_divider_v1(meta_model):
    if len(meta_model.get_property('lookups', default_value=[])) != 0:
        return meta_model.get_property('lookups')[0]['model_name']


def get_undivided_models_v0(meta_model):
    if meta_model.get_model_name() == "UndividedModel":
        try:
            return meta_model.get_property(prop_name="fields")[0].name.split(
                "_"
            )
        except IndexError:
            return []
    return []


def get_undivided_models_v1(meta_model):
    model_lookups = meta_model.get_property(
        prop_name='lookups', default_value=[]
    )
    if len(model_lookups) == 0:
        return [meta_model.get_model_name()]
    return []


divider_version_eq = {
    '0.0.0': {
        'get_divider_model': get_divider_v0,
        'get_undivided_models': get_undivided_models_v0,
    },
    '1.0.0': {
        'get_divider_model': get_divider_v1,
        'get_undivided_models': get_undivided_models_v1,
    },
}


def get_divider_fn(meta_model):
    #:  Get the divider function according to datamodel version and apply
    #:  on the meta_model to get the divider.
    version = getattr(meta_model, 'version', '0.0.0')
    fn = divider_version_eq[version]['get_divider_model']
    return fn(meta_model)


def get_divider():

    dividers_set = set(map(get_divider_fn, meta_models))

    #:  Remove None values from the set
    dividers_set.discard(None)

    if len(dividers_set) > 1:
        raise NotImplementedError(
            'Multiple dividers are not yet handeled by Concrete'
        )

    if len(dividers_set) == 0:
        return "DefaultDivider"

    return dividers_set.pop()


def get_undivided_models_fn(meta_model):
    #:  Get the undivided model function according to datamodel version and
    #:  apply on the meta_models to get the undivided models.
    version = getattr(meta_model, 'version', '0.0.0')
    fn = divider_version_eq[version]['get_undivided_models']
    return fn(meta_model)


def get_undivided_models():
    undivided_models = map(get_undivided_models_fn, meta_models)
    undivided_models_set = set(chain.from_iterable(undivided_models))

    return list(undivided_models_set)


divider = get_divider()
divider_field_name = divider.lower()

DIVIDER_MODEL = divider

UNDIVIDED_MODEL = get_undivided_models()

for meta_model in meta_models:
    if meta_model.get_model_name() in ["EntityDividerModel", "UndividedModel"]:
        logging.debug("Horrible patch for handling input specification")
        continue
    setattr(
        sys.modules[__name__],
        meta_model.get_model_name(),
        make_django_model(meta_model, divider),
    )
