# coding: utf-8

from django.apps import apps
from django.conf import settings
from django.contrib import admin
from django.utils.translation import ugettext_lazy as _
from concrete_datastore.concrete.meta import list_of_meta
from concrete_datastore.admin.admin_models import MetaUserAdmin, MetaAdmin
from concrete_datastore.admin.admin_site import get_admin_site
from concrete_datastore.concrete.models import (
    ConcreteRole,
    AuthToken,
    ConcretePermission,
)
from concrete_datastore.concrete.models import (
    divider,
    divider_field_name,
    UNDIVIDED_MODEL,
)
from concrete_datastore.interfaces.csv import csv_streaming_response


main_app = apps.get_app_config('concrete')

admin_site = get_admin_site()

admin_site.site_header = settings.ADMIN_HEADER
admin_site.site_url = None
for meta_model in list_of_meta:
    model_name = meta_model.get_model_name()
    if model_name in ["EntityDividerModel", "UndividedModel"]:
        continue

    models_fields = ('uid',)
    m2m_fields = []
    attrs = {}

    for field_name, field in meta_model.get_fields():
        models_fields += (field_name,)
        if field.f_type == 'ManyToManyField':
            m2m_fields.append(field_name)

    if model_name == 'User':
        list_display = (meta_model.get_property('m_list_display') or []) + [
            'level'
        ]
        #:  Model user necessarily have an email field. It should be
        #:  on top of the list display
        if 'email' in list_display:
            list_display.remove('email')
        list_display.insert(0, 'email')
        meta_user_admin_cls = MetaUserAdmin
        user_custom_fields = [
            field
            for field in models_fields
            if field not in MetaUserAdmin.user_fields
        ]
        user_custom_fields += ['external_auth']
        meta_user_admin_cls.fieldsets = (
            (_('User fields'), {'fields': user_custom_fields}),
        ) + meta_user_admin_cls.fieldsets
        ancestors = [meta_user_admin_cls]

    else:
        list_display = ['uid'] + (
            meta_model.get_property('m_list_display') or []
        )
        ancestors = [MetaAdmin]
        meta_fieldsets = MetaAdmin.fieldsets
        meta_model_fields = MetaAdmin.models_fields
        fieldsets = ((None, {'fields': models_fields}),) + meta_fieldsets
        if model_name != divider and model_name not in UNDIVIDED_MODEL:
            fieldsets += ((_('Scope'), {'fields': (divider_field_name,)}),)
        attrs.update({'fieldsets': fieldsets, 'filter_horizontal': m2m_fields})

    def make_list_filter(mm, mdl):
        def get_list_filter(self, request):
            initial_list_filter = mm.get_property('m_filter_fields') or []
            list_filter = ['creation_date', 'modification_date']
            for field_name in initial_list_filter:
                nb_objects = mdl.objects.values(field_name).distinct().count()
                if nb_objects <= settings.LIMIT_DEACTIVATE_FILTER_IN_ADMIN:
                    list_filter.append(field_name)
            return list_filter

        return get_list_filter

    def export_csv(self, request, queryset):
        fields = [f.name for f in queryset.model._meta.fields]
        return csv_streaming_response(
            request, queryset.values(*fields), fields
        )

    export_csv.short_description = 'Export CSV (UTF-8)'

    def make_actions():
        actions = ["export_csv"]
        return actions

    model = main_app.models[meta_model.get_model_name().lower()]

    attrs.update(
        {
            'list_display': list_display,
            'search_fields': meta_model.get_property('m_search_fields') or [],
            'get_list_filter': make_list_filter(meta_model, model),
            'actions': make_actions(),
            'export_csv': export_csv,
        }
    )
    admin_site.register(
        model,
        type(
            str('{}MetaAdmin'.format(meta_model.get_model_name())),
            tuple(ancestors),
            attrs,
        ),
    )


@admin.register(AuthToken, site=admin_site)
class AuthTokenAdmin(admin.ModelAdmin):
    ordering = ('expiration_date',)
    list_display = [
        'key',
        'user',
        'expired',
        'expiration_date',
        'last_action_date',
    ]
    search_fields = ['user__email', 'key']
    readonly_fields = ['key']
    list_filter = ['expiration_date', 'last_action_date', 'expired']
    fields = ['key', 'user', 'expired', 'expiration_date', 'last_action_date']


class SaveModelMixin:
    def save_model(self, request, obj, form, change):
        if change is False:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(ConcretePermission, site=admin_site)
class ConcretePermissionAdmin(admin.ModelAdmin, SaveModelMixin):
    list_display = ['uid', 'model_name', 'creation_date']
    search_fields = ['model_name']
    readonly_fields = [
        'uid',
        'created_by',
        'creation_date',
        'modification_date',
    ]
    date_hierarchy = 'creation_date'

    fields = [
        'uid',
        'model_name',
        'create_roles',
        'retrieve_roles',
        'update_roles',
        'delete_roles',
        'creation_date',
        'modification_date',
        'created_by',
    ]
    filter_horizontal = [
        'create_roles',
        'retrieve_roles',
        'update_roles',
        'delete_roles',
    ]


@admin.register(ConcreteRole, site=admin_site)
class ConcreteRoleAdmin(admin.ModelAdmin, SaveModelMixin):
    list_display = ['uid', 'name', 'creation_date']
    search_fields = ['name']
    readonly_fields = [
        'uid',
        'created_by',
        'creation_date',
        'modification_date',
    ]
    date_hierarchy = 'creation_date'

    fields = [
        'uid',
        'name',
        'users',
        'creation_date',
        'modification_date',
        'created_by',
    ]
    filter_horizontal = ['users']
