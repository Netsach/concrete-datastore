from django import forms
from django.db import IntegrityError
from django.contrib.contenttypes.models import ContentType
from django.contrib.admin import ModelAdmin
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.contenttypes import admin

from .models import CustomImageField


class Callable:
    def __init__(self, anycallable):
        self.__call__ = anycallable


class CustomImageFieldModel(object):
    """
    Abstract class
    """

    @property
    def get_custom_image_fields(self):
        """ Return a list of custom fields for this model """
        return CustomImageField.objects.filter(
            content_type=ContentType.objects.get_for_model(self)
        )

    def get_model_custom_image_fields(self):
        """Return a list of custom fields for this model, directly callable
        without an instance. Use like Foo.get_model_custom_fields(Foo)
        """
        return CustomImageField.objects.filter(
            content_type=ContentType.objects.get_for_model(self)
        )

    get_model_custom_image_fields = Callable(get_model_custom_image_fields)

    def get_custom_image_field(self, field_name):
        """Get a custom field object for this model
        field_name - Name of the custom field you want.
        """
        content_type = ContentType.objects.get_for_model(self)
        return CustomImageField.objects.get(
            content_type=content_type, name=field_name
        )
