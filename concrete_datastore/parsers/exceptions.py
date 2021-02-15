# coding: utf-8
from concrete_datastore.parsers.constants import (
    VERSIONS_ATTRIBUTES,
    AUTHORIZED_IP_PROTOCOLS,
)


class ModelManagerGenericException(Exception):
    """
    Main Exception class to handle errors in datamodel
    These exceptions are related to the version 1.0.0 of the datamodel
    definition. For further versions, adequate exceptions must be added
    """

    version = '1.0.0'
    code = ''
    message = ''

    def __str__(self):
        return f'[{self.code}]: {self.message}'


class MissingKeyForDefinition(ModelManagerGenericException):
    code = 'MISSING_KEY'

    def __init__(self, key, keys_list, resource_type, *args, **kwargs):
        self.message = (
            f'Cannot find key "{key}" for some {resource_type}. '
            f'Please make sure all your {resource_type.lower()}s definitions '
            f'contain at least the following keys: {keys_list}.'
        )


class UnknownDatamodelVersionError(ModelManagerGenericException):
    code = 'WRONG_VERSION'
    message = 'Key "version" of manifest should be 1.0.0.'


class UnknownIPProtocol(ModelManagerGenericException):
    code = 'UnknownIPProtocol'

    def __init__(self, protocol, source, field_name, *args, **kwargs):
        self.message = (
            f"Unknow protocol '{protocol}' for model {source}"
            f" and field {field_name}. "
            f"Authorized protocols are {AUTHORIZED_IP_PROTOCOLS}"
        )


class MissingRelationForModel(ModelManagerGenericException):
    code = 'MISSING_RELATION'

    def __init__(self, rel_type, source, target, field_name, *args, **kwargs):
        self.message = (
            f'Missing {rel_type} from {source} to {target} for field '
            f'"{field_name}". Please add it to {rel_type} section of your '
            'datamodel.'
        )


class DuplicatedRelationForModel(ModelManagerGenericException):
    code = 'DUPLICATED_RELATION'

    def __init__(self, rel_type, source, field_name, target, *args, **kwargs):
        self.message = (
            f'Relation duplicated in {rel_type} from "{source}" to "{target}" '
            f'for field "{field_name}" Please remove the duplicated relations '
            'to make sure only one exists.'
        )


class MissingPermissionsOrQueriesForModel(ModelManagerGenericException):
    def __init__(self, param_type, model_name, *args, **kwargs):
        self.code = f'MISSING_{param_type.upper()}'
        self.message = (
            f'Model "{model_name}" does not have any {param_type}. '
            'Please specify one for this model in your datamodel.'
        )


class DuplicatedPermissionsOrQueriesForModel(ModelManagerGenericException):
    def __init__(self, param_type, model_name, *args, **kwargs):
        self.code = f'DUPLICATED_{param_type.upper()}'
        self.message = (
            f'Duplicated {param_type} for model "{model_name}". '
            'Please make sure it is unique in your datamodel.'
        )


class NameNotAllowed(ModelManagerGenericException):
    code = 'NAME_NOT_ALLOWED'

    def __init__(self, name, resource_type, *args, **kwargs):
        self.message = (
            f'"{name}" cannot be used as a {resource_type} name. Please '
            f'select another name for this {resource_type} in your datamodel.'
        )


class DuplicatedFieldsError(ModelManagerGenericException):
    code = 'DUPLICATED_FIELDS'

    def __init__(self, field_name, model_name, *args, **kwargs):
        self.message = (
            f'Duplicated field "{field_name}" in model "{model_name}". '
            'Fields must have unique names. Please rename the duplicates.'
        )


class DuplicatedReverseForModel(ModelManagerGenericException):
    code = 'DUPLICATED_REVERSE'

    def __init__(self, name, reverse_name, *args, **kwargs):
        self.message = (
            f'Model "{name}" has more than one relation with the same reverse '
            f'name ({reverse_name}). Reverses should have a unique name for '
            'the same model. Please rename the duplicates.'
        )


class UnknownDatatypeForField(ModelManagerGenericException):
    code = 'UNKNOWN_DATATYPE'

    def __init__(self, field_name, model_name, datatype, *args, **kwargs):
        allowed_datatypes = list(
            VERSIONS_ATTRIBUTES[self.version]['equivalence_table'].keys()
        )
        self.message = (
            f'Field "{field_name}" of model "{model_name}" has an invalid '
            f'datatype ({datatype}). Please choose a valid datatype '
            f'from {allowed_datatypes}.'
        )


class ProtectedFieldNameError(ModelManagerGenericException):
    code = 'FIELD_NAME_NOT_ALLOWED'

    def __init__(self, field_name, model_name, *args, **kwargs):
        self.message = (
            f'"{field_name}" is a protected field for model "{model_name}" '
            'and cannot be redefined. Please rename it.'
        )


class ProtectedModelNameError(ModelManagerGenericException):
    code = 'MODEL_NAME_NOT_ALLOWED'

    def __init__(self, model_name, *args, **kwargs):
        self.message = (
            f'"{model_name}" is a protected model. You cannot use '
            'this name to define a new model. Please rename it.'
        )


class DuplicatedModelError(Exception):
    """
    This exception is deprecated and will be removed in further versions
    """

    pass
