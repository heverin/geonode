# -*- coding: utf-8 -*-
#########################################################################
#
# Copyright (C) 2016 OSGeo
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
#########################################################################

from django.contrib import admin
from django.contrib.admin import helpers
from django.conf import settings
from django.core.management import call_command
from django.template.response import TemplateResponse


from io import StringIO

from dal import autocomplete
from taggit.forms import TagField
from django import forms

from treebeard.admin import TreeAdmin
from treebeard.forms import movenodeform_factory

from modeltranslation.admin import TabbedTranslationAdmin

from geonode.base.models import (
    TopicCategory,
    SpatialRepresentationType,
    Region,
    RestrictionCodeType,
    ContactRole,
    Link,
    License,
    HierarchicalKeyword,
    MenuPlaceholder,
    Menu,
    MenuItem,
    CuratedThumbnail,
)
from django.http import HttpResponseRedirect

from geonode.base.widgets import TaggitSelect2Custom


def metadata_batch_edit(modeladmin, request, queryset):
    ids = ','.join([str(element.pk) for element in queryset])
    resource = queryset[0].class_name.lower()
    return HttpResponseRedirect(
        '/{}s/metadata/batch/{}/'.format(resource, ids))


metadata_batch_edit.short_description = 'Metadata batch edit'


def set_batch_permissions(modeladmin, request, queryset):
    ids = ','.join([str(element.pk) for element in queryset])
    resource = queryset[0].class_name.lower()
    return HttpResponseRedirect(
        '/{}s/permissions/batch/{}/'.format(resource, ids))


set_batch_permissions.short_description = 'Set permissions'


class LicenseAdmin(TabbedTranslationAdmin):
    model = License
    list_display = ('id', 'name')
    list_display_links = ('name',)


class TopicCategoryAdmin(TabbedTranslationAdmin):
    model = TopicCategory
    list_display_links = ('identifier',)
    list_display = (
        'identifier',
        'description',
        'gn_description',
        'fa_class',
        'is_choice')
    if settings.MODIFY_TOPICCATEGORY is False:
        exclude = ('identifier', 'description',)

    def has_add_permission(self, request):
        # the records are from the standard TC 211 list, so no way to add
        if settings.MODIFY_TOPICCATEGORY:
            return True
        else:
            return False

    def has_delete_permission(self, request, obj=None):
        # the records are from the standard TC 211 list, so no way to remove
        if settings.MODIFY_TOPICCATEGORY:
            return True
        else:
            return False


class RegionAdmin(TabbedTranslationAdmin):
    model = Region
    list_display_links = ('name',)
    list_display = ('code', 'name', 'parent')
    search_fields = ('code', 'name',)
    group_fieldsets = True


class SpatialRepresentationTypeAdmin(TabbedTranslationAdmin):
    model = SpatialRepresentationType
    list_display_links = ('identifier',)
    list_display = ('identifier', 'description', 'gn_description', 'is_choice')

    def has_add_permission(self, request):
        # the records are from the standard TC 211 list, so no way to add
        return False

    def has_delete_permission(self, request, obj=None):
        # the records are from the standard TC 211 list, so no way to remove
        return False


class RestrictionCodeTypeAdmin(TabbedTranslationAdmin):
    model = RestrictionCodeType
    list_display_links = ('identifier',)
    list_display = ('identifier', 'description', 'gn_description', 'is_choice')

    def has_add_permission(self, request):
        # the records are from the standard TC 211 list, so no way to add
        return False

    def has_delete_permission(self, request, obj=None):
        # the records are from the standard TC 211 list, so no way to remove
        return False


class ContactRoleAdmin(admin.ModelAdmin):
    model = ContactRole
    list_display_links = ('id',)
    list_display = ('id', 'contact', 'resource', 'role')
    list_editable = ('contact', 'resource', 'role')
    form = forms.modelform_factory(ContactRole, fields='__all__')


class LinkAdmin(admin.ModelAdmin):
    model = Link
    list_display_links = ('id',)
    list_display = ('id', 'resource', 'extension', 'link_type', 'name', 'mime')
    list_filter = ('resource', 'extension', 'link_type', 'mime')
    search_fields = ('name', 'resource__title',)
    form = forms.modelform_factory(Link, fields='__all__')


class HierarchicalKeywordAdmin(TreeAdmin):
    search_fields = ('name', )
    form = movenodeform_factory(HierarchicalKeyword)


class MenuPlaceholderAdmin(admin.ModelAdmin):
    model = MenuPlaceholder
    list_display = ('name', )


class MenuAdmin(admin.ModelAdmin):
    model = Menu
    list_display = ('title', 'placeholder', 'order')


class MenuItemAdmin(admin.ModelAdmin):
    model = MenuItem
    list_display = ('title', 'menu', 'order', 'blank_target', 'url')


class CuratedThumbnailAdmin(admin.ModelAdmin):
    model = CuratedThumbnail
    list_display = ('id', 'resource', 'img', 'img_thumbnail')


admin.site.register(TopicCategory, TopicCategoryAdmin)
admin.site.register(Region, RegionAdmin)
admin.site.register(SpatialRepresentationType, SpatialRepresentationTypeAdmin)
admin.site.register(RestrictionCodeType, RestrictionCodeTypeAdmin)
admin.site.register(ContactRole, ContactRoleAdmin)
admin.site.register(Link, LinkAdmin)
admin.site.register(License, LicenseAdmin)
admin.site.register(HierarchicalKeyword, HierarchicalKeywordAdmin)
admin.site.register(MenuPlaceholder, MenuPlaceholderAdmin)
admin.site.register(Menu, MenuAdmin)
admin.site.register(MenuItem, MenuItemAdmin)
admin.site.register(CuratedThumbnail, CuratedThumbnailAdmin)


class ResourceBaseAdminForm(autocomplete.FutureModelForm):

    keywords = TagField(widget=TaggitSelect2Custom('autocomplete_hierachical_keyword'))

    class Meta:
        pass
