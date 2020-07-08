# coding: utf-8
from django.conf import settings

from concrete_datastore.api.v1.exceptions import (
    PasswordInsecureValidationError,
)


class PasswordMinLengthValidation(object):
    """
    Validate whether the password is of a minimum length.
    """

    code = 'NOT_ENOUGH_CHARS'

    def __init__(self):
        self.min_length = settings.PASSWORD_MIN_LENGTH

    def validate(self, password, user=None):
        if len(password) < self.min_length:
            raise PasswordInsecureValidationError(
                message="The password must contain at least {} character(s).".format(
                    self.min_length
                ),
                code=self.code,
                params={'min_length': self.min_length},
            )

    def get_help_text(self):
        help_text = (
            "Your password must contain at least {min_length} character(s)."
        ).format(min_length=self.min_length)
        return help_text

    def get_help_text_fr(self):
        help_text = (
            "Votre mot de passe doit contenir au moins {min_length} caractère(s)"
        ).format(min_length=self.min_length)
        return help_text


class PasswordMinDigitsValidation(object):
    """
    Validate whether the password is of a minimum length.
    """

    code = 'NOT_ENOUGH_DIGITS'

    def __init__(self):
        self.min_digits = settings.PASSWORD_MIN_DIGITS

    def get_digits_count(self, password):
        count = 0
        for char in password:
            if char.isdigit():
                count += 1
        return count

    def validate(self, password, user=None):
        if self.get_digits_count(password) < self.min_digits:
            raise PasswordInsecureValidationError(
                message="The password must contain at least {} digit(s).".format(
                    self.min_digits
                ),
                code=self.code,
                params={'min_digits': self.min_digits},
            )

    def get_help_text(self):
        help_text = (
            "Your password must contain at least {min_digits} digit(s)."
        ).format(min_digits=self.min_digits)
        return help_text

    def get_help_text_fr(self):
        help_text = (
            "Votre mot de passe doit contenir au moins {min_digits} chiffre(s)"
        ).format(min_digits=self.min_digits)
        return help_text


class PasswordMinLowerValidation(object):
    """
    Validate whether the password is of a minimum length.
    """

    code = 'NOT_ENOUGH_LOWER'

    def __init__(self):
        self.min_lower = settings.PASSWORD_MIN_LOWER

    def get_lower_count(self, password):
        count = 0
        for char in password:
            if char.isdigit() is False and char.lower() == char:
                count += 1
        return count

    def validate(self, password, user=None):
        if self.get_lower_count(password) < self.min_lower:
            raise PasswordInsecureValidationError(
                message="The password must contain at least {} lower character(s).".format(
                    self.min_lower
                ),
                code=self.code,
                params={'min_lower': self.min_lower},
            )

    def get_help_text(self):
        help_text = (
            "Your password must contain at least {min_lower} lower character(s)."
        ).format(min_lower=self.min_lower)
        return help_text

    def get_help_text_fr(self):
        help_text = (
            "Votre mot de passe doit contenir au moins {min_lower} caractère(s) minuscule(s)"
        ).format(min_lower=self.min_lower)
        return help_text


class PasswordMinUpperValidation(object):
    """
    Validate whether the password is of a minimum length.
    """

    code = 'NOT_ENOUGH_UPPER'

    def __init__(self):
        self.min_upper = settings.PASSWORD_MIN_UPPER

    def get_upper_count(self, password):
        count = 0
        for char in password:
            if char.isdigit() is False and char.upper() == char:
                count += 1
        return count

    def validate(self, password, user=None):
        if self.get_upper_count(password) < self.min_upper:
            raise PasswordInsecureValidationError(
                message="The password must contain at least {} upper character(s).".format(
                    self.min_upper
                ),
                code=self.code,
                params={'min_upper': self.min_upper},
            )

    def get_help_text(self):
        help_text = (
            "Your password must contain at least {min_upper} upper character(s)."
        ).format(min_upper=self.min_upper)
        return help_text

    def get_help_text_fr(self):
        help_text = (
            "Votre mot de passe doit contenir au moins {min_upper} caractère(s) majuscule(s)"
        ).format(min_upper=self.min_upper)
        return help_text


class PasswordMinSpecialValidation(object):
    """
    Validate whether the password has a minimum of special characters.
    """

    code = 'NOT_ENOUGH_SPECIAL'

    def __init__(self):
        self.min_special = settings.PASSWORD_MIN_SPECIAL

    def get_special_count(self, password):
        count = 0
        for char in password:
            if char in settings.SPECIAL_CHARACTERS:
                count += 1
        return count

    def validate(self, password, user=None):
        if self.get_special_count(password) < self.min_special:
            raise PasswordInsecureValidationError(
                message=(
                    "The password must contain at least {min_special} special"
                    " character(s) from these : {special_list}"
                ).format(
                    min_special=self.min_special,
                    special_list=''.join(set(settings.SPECIAL_CHARACTERS)),
                ),
                code=self.code,
                params={'min_special': self.min_special},
            )

    def get_help_text(self):
        help_text = (
            "Your password must contain at least {min_special} special"
            " character(s) from these : {special_list}"
        ).format(
            min_special=self.min_special,
            special_list=''.join(set(settings.SPECIAL_CHARACTERS)),
        )
        return help_text

    def get_help_text_fr(self):
        help_text = (
            "Votre mot de passe doit contenir au moins {min_special} caractères spéciaux parmi ceux là: {special_list}"
        ).format(
            min_special=self.min_special,
            special_list=''.join(set(settings.SPECIAL_CHARACTERS)),
        )
        return help_text
