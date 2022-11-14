# coding: utf-8
from importlib import import_module
from django.conf import settings


def is_mfa_enabled(user):
    module_name, func_name = settings.MFA_RULE_PER_USER.rsplit('.', 1)
    module = import_module(module_name)
    use_mfa_rule = getattr(module, func_name)
    #: If the user has a totp_device, the mfa is enabled
    return use_mfa_rule(user=user) or user.totp_device is not None
