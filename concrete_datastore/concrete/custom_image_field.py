from django import forms
from django.db import IntegrityError
from django.contrib.contenttypes.models import ContentType
from django.contrib.admin import ModelAdmin
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.contenttypes import admin

from concrete_datastore.concrete.models import (
    CustomImageField,
    CustomImageFieldValue,
)


class Callable:
    def __init__(self, anycallable):
        self.__call__ = anycallable


class CustomImageFieldModel(object):
    """
    Abstract class
    """

    @property
    def get_custom_fields(self):
        """ Return a list of custom fields for this model """
        return CustomImageField.objects.filter(
            content_type=ContentType.objects.get_for_model(self)
        )

    def get_model_custom_fields(self):
        """Return a list of custom fields for this model, directly callable
        without an instance. Use like Foo.get_model_custom_fields(Foo)
        """
        return CustomImageField.objects.filter(
            content_type=ContentType.objects.get_for_model(self)
        )

    get_model_custom_fields = Callable(get_model_custom_fields)

    def get_custom_field(self, field_name):
        """Get a custom field object for this model
        field_name - Name of the custom field you want.
        """
        content_type = ContentType.objects.get_for_model(self)
        return CustomImageField.objects.get(
            content_type=content_type, name=field_name
        )

    def get_custom_value(self, field_name):
        """Get a value for a specified custom field
        field_name - Name of the custom field you want.
        """
        custom_field = self.get_custom_field(field_name)
        return CustomImageFieldValue.objects.get_or_create(
            field=custom_field, object_id=self.id
        )[0].value

    def set_custom_value(self, field_name, value):
        """Set a value for a specified custom field
        field_name - Name of the custom field you want.
        value - Value to set it to
        """
        custom_field = self.get_custom_field(field_name)
        custom_value = CustomImageFieldValue.objects.get_or_create(
            field=custom_field, object_id=self.id
        )[0]
        custom_value.value = value
        custom_value.save()
