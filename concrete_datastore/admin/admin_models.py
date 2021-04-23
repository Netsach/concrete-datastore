# coding: utf-8
from django.conf import settings
from django.contrib import admin
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.admin import UserAdmin

from concrete_datastore.admin.admin_form import (
    MyChangeUserForm,
    MyCreationUserForm,
)
from concrete_datastore.concrete.models import divider_field_name
from django.contrib.gis.admin import OSMGeoAdmin


class MetaUserAdmin(UserAdmin, OSMGeoAdmin):
    display_wkt = True
    models_fields = ()
    readonly_fields = ['uid', 'creation_date', 'modification_date']
    date_fields = ('creation_date', 'modification_date')
    subscriptions_fields = ('unsubscribe_all', 'unsubscribe_to')
    user_fields = (
        'uid',
        'email',
        'first_name',
        'last_name',
        'password',
        'user_level',
    )
    divider_field_name_plural = divider_field_name + 's'
    form = MyChangeUserForm
    add_form = MyCreationUserForm
    add_form_template = 'admin/add_form.html'
    add_fieldsets = (
        (
            None,
            {
                'classes': ('wide',),
                'fields': ('email', 'password1', 'password2'),
            },
        ),
    )
    fieldsets = (
        (None, {'fields': user_fields}),
        (_('Scope'), {'fields': (divider_field_name_plural,)}),
        (_('Dates'), {'fields': date_fields}),
        (_('Subscriptions'), {'fields': subscriptions_fields}),
    )
    if settings.ADMIN_SHOW_USER_PERMISSIONS is True:
        fieldsets += ((_('Permissions'), {'fields': ('user_permissions',)}),)
    filter_horizontal = (divider_field_name_plural, 'unsubscribe_to')
    ordering = ('email',)

    def save_model(self, request, obj, form, change):
        if change:
            # Seul le model user a un user_level
            if 'user_level' in form.cleaned_data:
                obj.email = obj.email.lower()
                obj.set_level(
                    level=form.cleaned_data.get('user_level'), commit=False
                )

        confirmation = obj.get_or_create_confirmation()
        if settings.AUTH_CONFIRM_EMAIL_ENABLE is False:
            confirmation.confirmed = True
            confirmation.save()
        else:
            if confirmation.link_sent is False:
                confirmation.send_link()
        super(MetaUserAdmin, self).save_model(request, obj, form, change)


class MetaAdmin(OSMGeoAdmin):
    display_wkt = True
    models_fields = ()
    date_fields = ('creation_date', 'modification_date')
    date_hierarchy = 'creation_date'
    readonly_fields = [
        'uid',
        'creation_date',
        'modification_date',
        'created_by',
    ]
    permissions = (
        'public',
        'created_by',
        ('can_view_users', 'can_view_groups'),
        ('can_admin_users', 'can_admin_groups'),
    )
    fieldsets = (
        (_('Dates'), {'fields': date_fields}),
        (_('Permissions'), {'fields': permissions}),
    )
    filter_horizontal = (
        'can_view_users',
        'can_view_groups',
        'can_admin_users',
        'can_admin_groups',
    )
    # En rajoutant un css sous la forme ci-dessous, on peut rajouter du css
    # à un model admin spécifique
    # css = {
    #     'all': (
    #         'admin/css/reset_css.css',
    #     )
    # }

    class Media:
        css = {}

    def save_model(self, request, obj, form, change):
        if change is False:
            obj.created_by = request.user
        super(MetaAdmin, self).save_model(request, obj, form, change)
