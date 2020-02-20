# coding: utf-8
from django.conf import settings

from concrete_datastore.parsers.loaders import loads_meta


default_meta_models = [
    # Model Email
    {
        "std.name": "Email",
        "std.specifier": "Model",
        "std.verbose_name": "Email",
        "std.verbose_name_plural": "Emails",
        "std.description": "Email",
        "ext.m_creation_minimum_level": "authenticated",
        "ext.m_retrieve_minimum_level": "superuser",
        "ext.m_update_minimum_level": "superuser",
        "ext.m_delete_minimum_level": "superuser",
        "ext.m_is_default_public": False,
        "ext.m_unicode": 'subject',
        "ext.m_list_display": ['subject', 'receiver'],
        "ext.m_search_fields": ['subject', 'body'],
        "ext.m_filter_fields": [],
        "std.fields": [
            {
                "std.name": "subject",
                "std.specifier": "Field",
                "std.verbose_name": "subject",
                "std.description": "subject of the email",
                "std.type": "data",
                "ext.f_type": "CharField",
                "ext.f_args": {'max_length': 250},
            },
            {
                "std.name": "resource_status",
                "std.specifier": "Field",
                "std.verbose_name": "Resource status",
                "std.description": "status of the resource email",
                "std.type": "data",
                "ext.f_type": "CharField",
                "ext.f_args": {
                    'max_length': 250,
                    'default': 'to-send',
                    'choices': (
                        ('to-send', 'Email should be sent'),
                        ('send-in-progress', 'Email sending'),
                        ('send-error', 'Error during sending'),
                        ('sent', 'Email sent'),
                    ),
                },
            },
            {
                "std.name": "resource_message",
                "std.specifier": "Field",
                "std.verbose_name": "Resource message",
                "std.description": "message of the resource email",
                "std.type": "data",
                "ext.f_type": "CharField",
                "ext.f_args": {'max_length': 250},
            },
            {
                "std.name": "body",
                "std.specifier": "Field",
                "std.verbose_name": "body",
                "std.description": "body of the email",
                "std.type": "data",
                "ext.f_type": "TextField",
                "ext.f_args": {},
            },
            {
                "std.name": "receiver",
                "std.specifier": "Field",
                "std.verbose_name": "receiver",
                "std.description": "receiver of the email",
                "std.type": "rel_single",
                "ext.f_type": "ForeignKey",
                "ext.f_args": {
                    'to': 'concrete.User',
                    'related_name': 'received_emails',
                    'null': False,
                    'blank': False,
                },
            },
        ],
    }
]


meta_models = loads_meta(settings.META_MODEL_DEFINITIONS) + loads_meta(
    default_meta_models
)


list_of_meta = list(
    filter(
        lambda x: x._specifier.name not in settings.DISABLED_MODELS,
        meta_models,
    )
)

meta_registered = {
    k: v
    for k, v in zip(
        map(lambda m: 'concrete.{}'.format(m._specifier.name), list_of_meta),
        list_of_meta,
    )
}


def make_unicode_method(meta_model):
    def __str__(self):
        model_field_name = meta_model.get_property('m_unicode')
        try:
            return str(getattr(self, model_field_name))
        except Exception:
            return '<{} {}>'.format(meta_model.get_model_name(), self.pk)

    return __str__


def get_meta_definition_by_model_name(model_name):
    for meta_definition in list_of_meta:
        if meta_definition.get_model_name() == model_name:
            return meta_definition
    raise AttributeError('No model named {}'.format(model_name))
