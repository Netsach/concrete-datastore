# coding: utf-8
from concrete_datastore.parsers.models import Model_V1
from concrete_datastore.parsers.meta import (
    make_model_cls,
    make_modelisation_cls,
)


def loads_models_v0(model_definitions):
    meta_models = []
    for meta_model_definition in model_definitions:
        meta_model_definition_copy = meta_model_definition.copy()
        meta_models += [make_model_cls(meta_model_definition_copy)]

    return meta_models


def loads_models_v1(model_definitions):
    try:
        modelisation = make_modelisation_cls(
            model_definitions, version='1.0.0', base=Model_V1
        )()
    except KeyError:
        raise KeyError('Invalid meta model definition')
    return modelisation.get_meta_models()  # pylint: disable=no-member


data_models_version = {"0.0.0": loads_models_v0, "1.0.0": loads_models_v1}


def loads_meta(model_definitions):
    if isinstance(model_definitions, (list, tuple)):
        return data_models_version["0.0.0"](model_definitions)
    try:
        version = model_definitions['manifest']['version']
    except KeyError:
        raise KeyError('Invalid meta model definition')

    load_func = data_models_version[version]
    return load_func(model_definitions)
