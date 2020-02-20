# coding: utf-8
from mock import MagicMock, patch
from django.test import TestCase
from django.conf import settings

from concrete_datastore.api.v1.serializers import make_custom_serializer_fields
from django.test import override_settings


@override_settings(DEBUG=True)
class MakeCustomSerializerTestCase(TestCase):
    def setUp(self):
        patch(
            'concrete_datastore.api.v1.serializers.make_related_serializer_class'
        ).start()
        pass

    def test_make_custom_field(self):
        CONCRETE = {
            "CONCRETE": {
                "SERIALIZERS": {
                    "model_name": {
                        "CUSTOM_FIELDS": {
                            "field_name": {
                                "type": "RelatedModelSerializer",
                                "to": "something",
                            }
                        }
                    }
                }
            }
        }
        # settings1 = settings
        vars(settings).update(CONCRETE)
        meta_model = MagicMock()
        meta_model.get_model_name = MagicMock(return_value="model_name")
        result = make_custom_serializer_fields(meta_model)
        self.assertEqual(list(result[0]), ['field_name'])
        self.assertIn('field_name', result[1])

    def test_make_custom_field_error(self):
        CONCRETE = {
            "CONCRETE": {
                "SERIALIZERS": {
                    "model_name": {
                        "CUSTOM_FIELDS": {
                            "field_name": {
                                "type": "OtherType",
                                "to": "something",
                            }
                        }
                    }
                }
            }
        }
        # settings1 = settings
        vars(settings).update(CONCRETE)
        meta_model = MagicMock()
        meta_model.get_model_name = MagicMock(return_value="model_name")
        with self.assertRaises(NotImplementedError):
            make_custom_serializer_fields(meta_model)

    def tearDown(self):
        patch.stopall()
