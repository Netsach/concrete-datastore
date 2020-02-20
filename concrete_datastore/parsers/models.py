# coding: utf-8
from slugify import slugify

from concrete_datastore.parsers.helpers import camel_case_to_dash_case


class Model:
    """
    Model base class
    """

    _specifier = None

    @classmethod
    def get_verbose_name(cls):
        return cls._specifier.std_verbose_name

    @classmethod
    def get_verbose_name_plural(cls):
        verbose_name_plural = cls.get_property('verbose_name_plural')
        if verbose_name_plural is None:
            verbose_name_plural = '{}s'.format(cls.get_verbose_name())
        return verbose_name_plural

    @classmethod
    def get_description(cls):
        return cls._specifier.std_description

    @classmethod
    def get_slugified_name(cls):
        return slugify(cls.get_model_name())

    @classmethod
    def get_model_name(cls):
        return cls._specifier.std_name

    @classmethod
    def get_dashed_case_class_name(cls):
        return camel_case_to_dash_case(cls.get_model_name())

    @classmethod
    def get_fields(cls):
        """
        Return a generator yielding field names
        """
        return ((f.std_name, f) for f in cls._specifier.std_fields)

    @classmethod
    def get_property(cls, prop_name, default_value=None):
        """
        Return a property of the model
        """
        return getattr(cls._specifier, prop_name, default_value)


class Model_V1:
    """
    Model base class
    """

    _specifier = None

    version = "1.0.0"

    @classmethod
    def get_verbose_name(cls):
        return getattr(
            cls._specifier, 'std_verbose_name', cls.get_model_name()
        )

    @classmethod
    def get_verbose_name_plural(cls):
        verbose_name_plural = cls.get_property('verbose_name_plural')
        if verbose_name_plural is None:
            verbose_name_plural = '{}s'.format(cls.get_verbose_name())
        return verbose_name_plural

    @classmethod
    def get_description(cls):
        return getattr(cls._specifier, 'std_description', '')

    @classmethod
    def get_slugified_name(cls):
        return slugify(cls.get_model_name())

    @classmethod
    def get_model_name(cls):
        return cls._specifier.name

    @classmethod
    def get_dashed_case_class_name(cls):
        return camel_case_to_dash_case(cls.get_model_name())

    @classmethod
    def get_fields(cls):
        """
        Return a generator yielding field names
        """
        return ((f.name, f) for f in cls._specifier.fields_spec)

    @classmethod
    def get_property(cls, prop_name, default_value=None):
        """
        Return a property of the model
        """
        return getattr(cls._specifier, prop_name, default_value)
