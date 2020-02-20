# coding: utf-8
from django.core.exceptions import ValidationError


class ConcreteBaseError(ValueError):
    pass


class PasswordInsecureValidationError(ValidationError, ConcreteBaseError):
    detail = 'PASSWORD_INSECURE'


class WrongEntityUIDError(ConcreteBaseError):
    detail = 'WRONG_ENTITY_UID'
