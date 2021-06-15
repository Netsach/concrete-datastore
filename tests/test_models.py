# coding: utf-8
from django.test import TestCase
from mock import MagicMock, patch
from concrete_datastore.concrete.meta import get_meta_definition_by_model_name
from concrete_datastore.concrete.models import (
    make_django_model,
)
from django.db import models
import uuid
from django.test import override_settings


from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse
from concrete_datastore.concrete.models import (
    CustomImageField,
    CustomImageFieldValue,
)


@override_settings(DEBUG=True)
class DeviderFieldTest(TestCase):
    def tearDown(self):
        patch.stopall()

    def test_get_meta_definition_by_model_name(self):
        with self.assertRaises(AttributeError):
            get_meta_definition_by_model_name('UnkNowModelNameForErrorTest')

    def test_make_django_model_for_user(self):
        patch(
            'concrete_datastore.concrete.models.get_common_fields',
            side_effect=[
                {
                    'uid': models.UUIDField(
                        primary_key=True, default=uuid.uuid4
                    ),
                    'modification_date': models.DateTimeField(
                        auto_now=True,
                        # default=timezone.now
                    ),
                    'creation_date': models.DateTimeField(
                        auto_now_add=True,
                        # default=timezone.now
                    ),
                    'public': models.BooleanField(default=True),
                }
            ],
        ).start()

        patch(
            'concrete_datastore.concrete.models.UNDIVIDED_MODEL',
            side_effect=[[u'Test']],
        ).start()

        meta_model = MagicMock()
        divider = 'divider'
        key = 'key'
        value = MagicMock()
        value.f_type = str('ForeignKey')
        value.f_args = {'to': 'self', 'on_delete': 'CASCADE'}
        meta_model.get_model_name = MagicMock(
            side_effect=[
                str('some_model'),
                str('User'),
                str('test'),
                str('Test'),
                str('Test'),
                str('Test'),
            ]
        )
        meta_model.get_property = MagicMock(return_value=str('attribute'))
        meta_model.get_fields = MagicMock(return_value=((key, value),))
        meta_model.version = None
        make_django_model(meta_model=meta_model, divider=divider)

    def test_make_django_model_for_divider(self):
        patch(
            'concrete_datastore.concrete.models.get_common_fields',
            side_effect=[
                {
                    'uid': models.UUIDField(
                        primary_key=True, default=uuid.uuid4
                    ),
                    'modification_date': models.DateTimeField(
                        auto_now=True,
                        # default=timezone.now
                    ),
                    'creation_date': models.DateTimeField(
                        auto_now_add=True,
                        # default=timezone.now
                    ),
                    'public': models.BooleanField(default=True),
                }
            ],
        ).start()

        meta_model = MagicMock()
        divider = 'divider'
        key = 'key'
        value = MagicMock()
        value.f_type = str('ForeignKey')
        value.f_args = {'to': 'self', 'on_delete': 'CASCADE'}
        meta_model.get_model_name = MagicMock(return_value=str('divider'))
        meta_model.get_property = MagicMock(return_value=str('attribute'))
        meta_model.get_fields = MagicMock(return_value=((key, value),))
        meta_model.version = None
        make_django_model(meta_model=meta_model, divider=divider)


@override_settings(DEBUG=True)
class CustomFieldTest(TestCase):
    def setUp(self):

        # custom_image_field_ct = ContentType.objects.get(
        #     app_label="custom_field", model="customfield"
        # )
        self.custom_image_field_jpg = CustomImageField.objects.create(
            name="jpg image",
            # content_type=custom_image_field_ct,
            filename="image.jpg",
        )
        self.custom_image_field_svg = CustomImageField.objects.create(
            name="svg image",
            # content_type=custom_image_field_ct,
            filename="image.svg",
        )
        self.custom_image_field_txt = CustomImageField.objects.create(
            name="txt image",
            # content_type=custom_image_field_ct,
            filename="image.txt",
        )
        user = User.objects.create_user("test", "test@netsach.com")
        user.set_password("test")
        user.is_superuser = True
        user.save()
        self.client.login(username="test", password="test")

    # def test_validation(self):
    #     custom_value = CustomFieldValue.objects.create(
    #         field=self.custom_field,
    #         value="5",
    #         object_id=self.custom_field.id,
    #     )
    #     custom_value.clean()
    #     custom_value.save()
    #     self.assertEquals(custom_value.value, "5")
    #     custom_value.value = "fdsf"
    #     try:
    #         custom_value.clean()
    #         self.fail("Was able to save string as custom integer field!")
    #     except ValidationError:
    #         pass

    def test_validation(self):
        self.assertEqual(self.custom_image_field_jpg, 'image.jpg')
