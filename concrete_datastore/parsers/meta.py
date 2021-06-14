# coding: utf-8
import uuid
import logging
from collections import namedtuple, defaultdict
from copy import deepcopy
from keyword import iskeyword
from six import with_metaclass
from django.core.validators import validate_ipv46_address
from concrete_datastore.parsers.exceptions import (
    UnknownDatamodelVersionError,
    MissingRelationForModel,
    DuplicatedRelationForModel,
    MissingPermissionsOrQueriesForModel,
    DuplicatedPermissionsOrQueriesForModel,
    NameNotAllowed,
    DuplicatedFieldsError,
    DuplicatedReverseForModel,
    UnknownDatatypeForField,
    MissingKeyForDefinition,
    ProtectedModelNameError,
    ProtectedFieldNameError,
    UnknownIPProtocol,
)
from concrete_datastore.parsers.validators import validate_specifier
from concrete_datastore.parsers.constants import (
    VERSIONS_ATTRIBUTES,
    CONCRETE_USER_PROTECTED_FIELDS,
    CONCRETE_MODELS_PROTECTED_FIELDS,
    CONCRETE_CUSTOM_MODELS,
    PROTOCOL_EQUIVALENCE,
    AUTHORIZED_IP_PROTOCOLS,
)
from concrete_datastore.parsers.models import Model
from concrete_datastore.parsers.fields import (
    field_descriptors,
    get_field_descriptor,
)
from concrete_datastore.parsers.helpers import replace_prefix, remove_prefix


class DynamicMetaClass(type):
    def __new__(cls, name, bases, clsdict):
        msg = 'Creating new Dynamic Class {}'.format(name)
        logging.debug(msg)

        if 'specifier' not in clsdict:
            raise RuntimeError('Missing specifier in class {}'.format(name))

        specifier_dict = clsdict['specifier']
        validate_specifier(specifier_dict=specifier_dict)

        dyn_class_name = specifier_dict['std.name']
        attr_names = list(map(replace_prefix, specifier_dict.keys()))
        attr_names.extend(map(remove_prefix, specifier_dict.keys()))
        struct_name = dyn_class_name.title()
        struct = namedtuple(struct_name, attr_names)
        struct_kwargs = {
            replace_prefix(k): v for k, v in specifier_dict.items()
        }
        struct_kwargs.update(
            {remove_prefix(k): v for k, v in specifier_dict.items()}
        )
        clsdict['_specifier'] = struct(**struct_kwargs)
        clsdict.pop('specifier')

        msg = 'Created {} with structure {}'.format(
            name, clsdict['_specifier']
        )
        logging.debug(msg)

        return type.__new__(cls, name, bases, clsdict)


def make_cls(spec, base, prefix):
    dyn_class_name = spec['std.name']

    def __init__(self, *args, **kwargs):
        self._uid = uuid.uuid4()
        super(self.__class__, self).__init__(*args, **kwargs)

    def __hash__(self):
        return self._uid.int

    return type(
        dyn_class_name.title(),
        (with_metaclass(DynamicMetaClass, base),),
        {'specifier': spec, '__init__': __init__, '__hash__': __hash__},
    )


def make_field_cls(spec, base=object):
    return make_cls(spec, base, prefix='Field')


def make_model_cls(spec, base=Model):
    fields = []
    for field_spec in spec['std.fields']:
        validate_specifier(field_spec)
        field_type = field_spec['std.type']
        field_cls = make_field_cls(
            field_spec, base=field_descriptors[field_type]
        )
        field_instance = field_cls(name=field_cls._specifier.std_name)
        fields.append((field_cls._specifier.std_name, field_instance))

    spec['std.fields'] = [f[1]._specifier for f in fields]
    model_cls = make_cls(spec, base, prefix='')

    # From 0.3.0 (incompatible) :
    # model_cls = make_cls(spec, base, prefix='Model')

    for name, field in fields:
        setattr(model_cls, name, field)
    return model_cls


def make_modelisation_cls(modelisation_spec, version, base=Model):
    spec = deepcopy(modelisation_spec)

    manifest = spec['manifest']
    data_modeling = manifest['data_modeling']

    models = data_modeling['models']

    many_to_many_relations = data_modeling['many_to_many_relations']
    one_to_many_relations = data_modeling['one_to_many_relations']
    permissions = data_modeling['permissions']
    resource_queries = data_modeling['resource_queries']

    relations = {"m2m": many_to_many_relations, "fk": one_to_many_relations}
    attrs = VERSIONS_ATTRIBUTES[version]

    def get_permissions(permission_dict, version):
        if version != '1.0.0':
            raise UnknownDatamodelVersionError()
        minimum_levels = {}
        for perm, level in permission_dict['minimum_levels'].items():
            key = 'creation' if perm == 'create' else perm
            minimum_levels.update({f'm_{key}_minimum_level': level})
        return minimum_levels

    def get_resource_queries(resource_dict, version):
        if version != '1.0.0':
            raise UnknownDatamodelVersionError()
            # Ordering fields default value is display_fields to stay
            # retrocompatible
        return {
            'm_search_fields': resource_dict['search_fields'],
            'm_filter_fields': resource_dict['filter_fields'],
            'm_ordering_fields': resource_dict.get(
                'ordering_fields', resource_dict['display_fields']
            )
            + ['creation_date', 'modification_date'],
            'm_distance_filter_field': resource_dict.get(
                'distance_filter_field', ''
            ),
            'm_export_fields': resource_dict['export_fields'],
            'm_list_display': resource_dict['display_fields']
            + ['creation_date', 'modification_date'],
        }

    def get_relation_for_field(
        self,
        f_type,
        src_field,
        src_model_uid,
        src_model_name,
        target_model_name,
        target_model_uid,
    ):
        if f_type == 'fk':
            rel_type = 'one_to_many_relations'
        elif f_type == 'm2m':
            rel_type = 'many_to_many_relations'
        relation_elements = list(
            filter(
                lambda x: x['source_field'] == src_field
                and x['source_model'][self.element_id] == src_model_uid
                and x['target_model'][self.element_id] == target_model_uid,
                relations[f_type],
            )
        )
        if len(relation_elements) == 0:
            raise MissingRelationForModel(
                rel_type=rel_type,
                source=src_model_name,
                target=target_model_name,
                field_name=src_field,
            )
        if len(relation_elements) > 1:
            raise DuplicatedRelationForModel(
                rel_type=rel_type,
                source=src_model_name,
                target=target_model_name,
                field_name=src_field,
            )
        rel = relation_elements[0]
        rel_model_name = rel['target_model']['name']
        return (f'concrete.{rel_model_name}', rel.get('onDelete', 'PROTECT'))

    def get_meta_models(self):
        meta_models = []
        self.models_attrs = defaultdict(lambda: defaultdict(list))
        for meta_model_definition in models:
            self.validate_specifier(meta_model_definition)
            model_name = meta_model_definition[self.element_name]
            if model_name in CONCRETE_CUSTOM_MODELS:
                raise ProtectedModelNameError(model_name=model_name)
            if iskeyword(model_name):
                raise NameNotAllowed(name=model_name, resource_type='model')
            model_permissions = self.get_parameter_for_model(
                model_spec=meta_model_definition,
                parameter_dict=permissions,
                param_type='permissions',
            )

            #:  For now, if the modelisation does not contain a
            #:  'resource_queries' field, we set all of search, filter, export
            #:  and list fields to all the fields of the model
            for field in meta_model_definition[self.fields_spec]:
                self.validate_specifier(field, spec_type='Field')
                field_name = field[self.element_name]
                if iskeyword(field_name):
                    raise NameNotAllowed(
                        name=field_name, resource_type='field'
                    )
                protected_user_field = (
                    model_name.lower() == 'user'
                    and field_name in CONCRETE_USER_PROTECTED_FIELDS
                )
                custom_model_protected_field = (
                    model_name.lower() != 'user'
                    and field_name in CONCRETE_MODELS_PROTECTED_FIELDS
                )
                if protected_user_field or custom_model_protected_field:
                    raise ProtectedFieldNameError(
                        field_name=field_name, model_name=model_name
                    )

                if (
                    field_name
                    in self.models_attrs[model_name][self.fields_spec]
                ):
                    raise DuplicatedFieldsError(
                        field_name=field_name, model_name=model_name
                    )
                self.models_attrs[model_name][self.fields_spec].append(
                    field_name
                )
            all_fields = [
                field[self.element_name]
                for field in meta_model_definition[self.fields_spec]
                if field[self.field_type_spec]
                in [
                    'bool',
                    'txt',
                    'text',
                    'char',
                    'url',
                    'float',
                    'datetime',
                    'date',
                    'int',
                    'fk',
                    'ip',
                ]
                #: we should consider only simple types
            ]
            default_resource_queries = {
                'search_fields': all_fields,
                'filter_fields': all_fields,
                'export_fields': all_fields,
                'display_fields': all_fields,
            }
            model_resource_queries = self.get_parameter_for_model(
                model_spec=meta_model_definition,
                parameter_dict=resource_queries,
                param_type='ressource_queries',
                default=default_resource_queries,
            )
            meta_models += [
                self.make_model_cls(
                    meta_model_definition,
                    model_permissions,
                    model_resource_queries,
                )
            ]
        return meta_models

    def make_model_cls(self, spec, permissions, resource_queries):
        fields = []
        for field_spec in spec[self.fields_spec]:
            field_type = field_spec[self.field_type_spec]
            field_cls = self.make_field_cls(
                field_spec=field_spec,
                model_name=spec[self.element_name],
                base=get_field_descriptor(field_type),
                model_uid=spec['uid'],
            )
            field_instance = field_cls(name=field_cls._specifier.name)
            fields.append((field_cls._specifier.name, field_instance))

        spec['fields_spec'] = [f[1]._specifier for f in fields]
        model_cls = self.make_cls(
            spec=spec,
            base=base,
            permissions=permissions,
            resource_queries=resource_queries,
        )

        for name, field in fields:
            setattr(model_cls, name, field)
        return model_cls

    def validate_specifier(self, field_spec, spec_type='Model'):
        specifier_keys = self.std_verifier[spec_type]

        for key in specifier_keys:
            if key not in field_spec:
                raise MissingKeyForDefinition(
                    key=key, keys_list=specifier_keys, resource_type=spec_type
                )

    def make_field_cls(
        self, field_spec, model_name, base=object, model_uid=None
    ):
        return self.make_cls(
            field_spec,
            base,
            specifier='Field',
            model_name=model_name,
            model_uid=model_uid,
        )

    def update_specifier_data(
        self,
        specifier,
        spec,
        model_name,
        model_uid,
        permissions=None,
        resource_queries=None,
    ):
        if specifier == 'Field':
            datatype = spec.pop(self.field_type_spec)
            if datatype not in self.equivalence_table.keys():
                raise UnknownDatatypeForField(
                    field_name=spec[self.element_name],
                    model_name=model_name,
                    datatype=datatype,
                )
            spec.update({'f_type': self.equivalence_table[datatype]})
            attributes = spec.pop('attributes')
            if 'allow_empty' in attributes.keys():
                allow_empty = attributes.pop('allow_empty')
                attributes.update({'null': allow_empty, 'blank': allow_empty})
            if datatype == 'char':
                attributes.setdefault('max_length', 250)
            if datatype == 'ip':
                attributes.setdefault('protocol', 'ipv4_6')
                protocol = attributes['protocol'].lower()
                if protocol not in AUTHORIZED_IP_PROTOCOLS:
                    raise UnknownIPProtocol(
                        protocol, model_name, spec[self.element_name]
                    )
                default_ip = attributes.get('default')
                if default_ip:
                    #: Raise Validation Error if the default IP is invalid
                    validate_ipv46_address(default_ip)
                attributes['protocol'] = PROTOCOL_EQUIVALENCE[protocol]
            if datatype in ['fk', 'm2m']:
                field_type = (
                    f'rel_{"single" if datatype == "fk" else "iterable"}'
                )
                target_field = (
                    attributes.pop('reverse')
                    if 'reverse' in attributes.keys()
                    else None
                )
                target_model_name = attributes['to'][self.element_name]
                if (
                    target_field
                    in self.models_attrs[target_model_name]['reverses']
                ):
                    raise DuplicatedReverseForModel(
                        name=model_name, reverse_name=target_field
                    )
                self.models_attrs[target_model_name]['reverses'].append(
                    target_field
                )
                rel_model, on_delete_rule = self.get_relation_for_field(
                    f_type=datatype,
                    src_field=spec[self.element_name],
                    src_model_uid=model_uid,
                    src_model_name=model_name,
                    target_model_name=target_model_name,
                    target_model_uid=attributes['to'][self.element_id],
                )
                attributes.update({'to': rel_model})
                attributes.update(
                    {'on_delete': on_delete_rule}
                ) if datatype == 'fk' else None
                attributes.update(
                    {'related_name': target_field}
                ) if target_field is not None else None

            else:
                field_type = 'data'

            spec.update({'f_args': attributes})
            spec.update({'type': field_type})

        elif specifier == 'Model':
            spec.update({'name': spec[self.element_name]})
            spec.update({'lookups': permissions['lookups']})
            spec.update(get_resource_queries(resource_queries, self.version))
            spec.update(get_permissions(permissions, self.version))
            spec.update({'m_unique_together': spec.get('unique_together', [])})
            spec.update({'m_unicode': spec.get('representation_field', '')})
            spec.update(
                {'m_is_default_public': spec.get('is_default_public', False)}
            )

    def get_parameter_for_model(
        self, model_spec, param_type, parameter_dict, default=None
    ):
        model_parameter = list(
            filter(
                lambda x: x['model_uid'] == model_spec[self.element_id],
                parameter_dict,
            )
        )
        if len(model_parameter) == 0:
            if default is not None:
                return default
            raise MissingPermissionsOrQueriesForModel(
                param_type=param_type, model_name=model_spec[self.element_name]
            )
        if len(model_parameter) > 1:
            raise DuplicatedPermissionsOrQueriesForModel(
                param_type=param_type, model_name=model_spec[self.element_name]
            )
        return model_parameter[0]

    def make_cls(
        self,
        spec,
        base,
        specifier='Model',
        model_name=None,
        model_uid=None,
        permissions=None,
        resource_queries=None,
    ):
        spec_copy = deepcopy(spec)
        self.update_specifier_data(
            specifier=specifier,
            spec=spec_copy,
            model_name=model_name,
            model_uid=model_uid,
            permissions=permissions,
            resource_queries=resource_queries,
        )

        class DynamicMetaClass(type):
            def __new__(cls, name, bases, clsdict):
                msg = 'Creating new Dynamic Class {}'.format(name)
                logging.debug(msg)

                if 'specifier' not in clsdict:
                    raise RuntimeError(
                        'Missing specifier in class {}'.format(name)
                    )
                specifier_dict = clsdict['specifier']

                dyn_class_name = specifier_dict[self.element_name]
                attr_names = list(specifier_dict.keys())

                struct_name = dyn_class_name
                struct = namedtuple(struct_name, attr_names)
                clsdict['_specifier'] = struct(**specifier_dict)
                clsdict.pop('specifier')

                msg = 'Created {} with structure {}'.format(
                    name, clsdict['_specifier']
                )
                logging.debug(msg)

                return type.__new__(cls, name, bases, clsdict)

        dyn_class_name = spec_copy[self.element_name]

        def __init__(self, *args, **kwargs):
            self._uid = uuid.uuid4()
            super(self.__class__, self).__init__(*args, **kwargs)

        def __hash__(self):
            return self._uid.int

        return type(
            dyn_class_name,
            (with_metaclass(DynamicMetaClass, base),),
            {
                'specifier': spec_copy,
                '__init__': __init__,
                '__hash__': __hash__,
            },
        )

    attrs.update(
        {
            'version': version,
            'get_meta_models': get_meta_models,
            'make_model_cls': make_model_cls,
            'make_field_cls': make_field_cls,
            'make_cls': make_cls,
            'validate_specifier': validate_specifier,
            'update_specifier_data': update_specifier_data,
            'get_parameter_for_model': get_parameter_for_model,
            'get_relation_for_field': get_relation_for_field,
        }
    )

    return type('ModelisationClass_{}'.format(version), (object,), attrs)
