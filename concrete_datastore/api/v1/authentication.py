# coding: utf-8
import pendulum
from django.utils.translation import gettext_lazy as _
from django.conf import settings

from rest_framework import authentication
from rest_framework import exceptions

from concrete_datastore.concrete.models import (  # pylint:disable=E0611
    SecureConnectToken,
    SecureConnectCode,
    AuthToken,
    Group,
)


def default_mfa_rule(user):
    return settings.USE_TWO_FACTOR_AUTH and user.is_at_least_admin


def default_backend_group_creation_rule(user, groups):
    for group_name in groups:
        group, created = Group.objects.get_or_create(name=group_name)
        user.concrete_groups.add(group)


def expire_temporary_tokens(user):
    # TODO: Get all temporary tokens from user and expire those out of date
    temp_token_expiry_seconds = getattr(
        settings, 'TWO_FACTOR_CODE_TIMEOUT_SECONDS', 600
    )
    now = pendulum.now('utc')
    expiry_token_limit = now.subtract(seconds=temp_token_expiry_seconds)
    user.temporary_tokens.filter(
        expired=False, creation_date__lte=expiry_token_limit
    ).update(expired=True)


def api_token_has_expired(token):
    if getattr(token, 'expired', False) is True:
        token.delete()
        return True
    token_can_expire = settings.API_TOKEN_EXPIRY > 0
    extra_period = settings.EXPIRY_EXTRA_PERIOD
    if token_can_expire:
        now = pendulum.now('utc')
        expiration_date = pendulum.instance(token.expiration_date)
        expiry_period_over = now > expiration_date
        expiry_spare_period_over = (
            extra_period == 0
            or now.diff(token.last_action_date).in_minutes() > extra_period
        )
        token_expired = expiry_period_over and expiry_spare_period_over
        if token_expired:
            token.delete()
            return True
    return False


def ensure_secure_connect_instance_is_not_expired(
    instance, expiration_limit_in_seconds
):
    # if the instance is not expired, return True
    # false otherwise
    if expiration_limit_in_seconds:
        now = pendulum.now('utc')
        secure_connect_instance_expired = (
            now.diff(instance.creation_date).in_seconds()
            >= expiration_limit_in_seconds
        )
        if secure_connect_instance_expired:
            instance.expired = True
            instance.save()
            return False
    return True


class TokenExpiryAuthentication(authentication.TokenAuthentication):
    def authenticate_credentials(self, key):
        model = AuthToken
        try:
            token = model.objects.select_related('user').get(key=key)
        except model.DoesNotExist:
            raise exceptions.AuthenticationFailed(_('Invalid token.'))

        if not token.user.is_active:
            raise exceptions.AuthenticationFailed(
                _('User inactive or deleted.')
            )

        if api_token_has_expired(token):
            raise exceptions.AuthenticationFailed(_('Token expired'))
        # Check if the secure token is expired and expire in database
        for secure_token in SecureConnectToken.objects.filter(
            user=token.user, expired=False
        ):
            ensure_secure_connect_instance_is_not_expired(
                secure_token, settings.SECURE_CONNECT_TOKEN_EXPIRY_TIME_SECONDS
            )
        # Check if the secure token is expired and expire in database
        for secure_code in SecureConnectCode.objects.filter(
            user=token.user, expired=False
        ):
            ensure_secure_connect_instance_is_not_expired(
                secure_code, settings.SECURE_CONNECT_CODE_EXPIRY_TIME_SECONDS
            )

        return (token.user, token)


class URLTokenExpiryAuthentication(TokenExpiryAuthentication):
    """
    This class allow a user to authenticate using the query param
    c_auth_with_token in the URL i.e. by appending ?c_auth_with_token=<value>
    """

    def authenticate(self, request):
        token = request.GET.get('c_auth_with_token', '')
        if not token:
            return

        if len(token) != 40:
            msg = _('Invalid token : {}'.format(repr(token)))
            raise exceptions.AuthenticationFailed(msg)

        return self.authenticate_credentials(token)
