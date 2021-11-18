# coding: utf-8
from tempfile import NamedTemporaryFile
from django.test import TestCase, override_settings
from concrete_datastore.settings.utils import load_datamodel
from concrete_datastore.parsers.exceptions import (
    UnknownIPProtocol,
    DuplicatedRelationForModel,
    MissingPermissionsOrQueriesForModel,
    DuplicatedPermissionsOrQueriesForModel,
    NameNotAllowed,
    DuplicatedFieldsError,
)
from concrete_datastore.parsers.loaders import loads_meta
from tests.fake_yaml_content import (
    YAML_CONTENT_ERROR,
    YAML_CONTENT_UNKNOWN_IP_PROTOCOL,
    YAML_CONTENT_DUPLICATE_RELATION,
    YAML_CONTENT_MISSING_PERMISSIONS,
    YAML_CONTENT_DUPLICATE_PERMISSIONS,
    YAML_CONTENT_NAME_NOT_ALLOWED,
    YAML_CONTENT_DUPLICATE_FIELD,
)


@override_settings(DEBUG=True)
class TestLoadDatamodel(TestCase):
    def test_meta_model_not_yaml(self):
        #: Use an empty file so the yaml load fails
        with NamedTemporaryFile(suffix=".txt") as fp:
            fp.write(YAML_CONTENT_ERROR.encode('utf-8'))
            fp.seek(0)
            with self.assertRaises(SystemExit):
                load_datamodel(fp.name)

    def test_meta_model_file_does_not_exist(self):
        with self.assertRaises(SystemExit):
            load_datamodel('/tmp/FAKE_FILE.yaml')

    def test_meta_model_wrong_ip_protocol(self):
        with NamedTemporaryFile(suffix=".yaml") as fp:
            fp.write(YAML_CONTENT_UNKNOWN_IP_PROTOCOL.encode('utf-8'))
            fp.seek(0)
            with self.assertRaises(UnknownIPProtocol):
                datamodel = load_datamodel(fp.name)
                loads_meta(datamodel)

    def test_meta_model_duplicated_relation(self):
        with NamedTemporaryFile(suffix=".yaml") as fp:
            fp.write(YAML_CONTENT_DUPLICATE_RELATION.encode('utf-8'))
            fp.seek(0)
            with self.assertRaises(DuplicatedRelationForModel):
                datamodel = load_datamodel(fp.name)
                loads_meta(datamodel)

    def test_meta_model_missing_permissions(self):
        with NamedTemporaryFile(suffix=".yaml") as fp:
            fp.write(YAML_CONTENT_MISSING_PERMISSIONS.encode('utf-8'))
            fp.seek(0)
            with self.assertRaises(MissingPermissionsOrQueriesForModel):
                datamodel = load_datamodel(fp.name)
                loads_meta(datamodel)

    def test_meta_model_duplicate_permissions(self):
        with NamedTemporaryFile(suffix=".yaml") as fp:
            fp.write(YAML_CONTENT_DUPLICATE_PERMISSIONS.encode('utf-8'))
            fp.seek(0)
            with self.assertRaises(DuplicatedPermissionsOrQueriesForModel):
                datamodel = load_datamodel(fp.name)
                loads_meta(datamodel)

    def test_meta_model_name_not_allowed(self):
        with NamedTemporaryFile(suffix=".yaml") as fp:
            fp.write(YAML_CONTENT_NAME_NOT_ALLOWED.encode('utf-8'))
            fp.seek(0)
            with self.assertRaises(NameNotAllowed):
                datamodel = load_datamodel(fp.name)
                loads_meta(datamodel)

    def test_meta_model_duplicate_field(self):
        with NamedTemporaryFile(suffix=".yaml") as fp:
            fp.write(YAML_CONTENT_DUPLICATE_FIELD.encode('utf-8'))
            fp.seek(0)
            with self.assertRaises(DuplicatedFieldsError):
                datamodel = load_datamodel(fp.name)
                loads_meta(datamodel)
