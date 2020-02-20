# coding: utf-8
from django.conf import settings


def test_mfa_rule_manager(user):
    return settings.USE_TWO_FACTOR_AUTH and user.is_at_least_staff


def test_mfa_rule_simpleuser(user):
    return settings.USE_TWO_FACTOR_AUTH and user.is_authenticated


def test_mfa_rule_admin(user):
    return settings.USE_TWO_FACTOR_AUTH and user.is_at_least_admin


def test_mfa_rule_superuser(user):
    return settings.USE_TWO_FACTOR_AUTH and user.is_superuser
