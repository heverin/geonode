#########################################################################
#
# Copyright (C) 2020 OSGeo
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
import logging
from django.contrib.auth import get_user_model

from rest_framework import permissions
from rest_framework.filters import BaseFilterBackend
from geonode.security.permissions import BASIC_MANAGE_PERMISSIONS, DOWNLOAD_PERMISSIONS, EDIT_PERMISSIONS, VIEW_PERMISSIONS
from django.contrib.auth.models import Group
from geonode.groups.conf import settings as groups_settings

from geonode.security.utils import (
    get_users_with_perms,
    get_resources_with_perms)
from geonode.groups.models import GroupProfile
from rest_framework.permissions import DjangoModelPermissions
from rest_framework.exceptions import NotFound
from guardian.shortcuts import get_objects_for_user
from itertools import chain
from guardian.shortcuts import get_groups_with_perms

logger = logging.getLogger(__name__)


class IsSelf(permissions.BasePermission):

    """ Grant permission only if the current instance is the request user.
    Used to allow users to edit their own account, nothing to others (even
    superusers).
    """

    def has_permission(self, request, view):
        """ Always return False here.
        The fine-grained permissions are handled in has_object_permission().
        """
        return False

    def has_object_permission(self, request, view, obj):
        user = request.user
        if user and isinstance(obj, get_user_model()) and obj.pk == user.pk:
            return True

        return False


class IsSelfOrReadOnly(IsSelf):

    """ Grant permissions if instance *IS* the request user, or read-only.
    Used to allow users to edit their own account, and others to read.
    """

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True

        return IsSelf.has_object_permission(self, request, view, obj)


class IsSelfOrAdmin(IsSelf):

    """ Grant R/W to self and superusers/staff members. Deny others. """

    def has_permission(self, request, view):
        user = request.user
        if user and (user.is_superuser or user.is_staff):
            return True

        return IsSelf.has_permission(self, request, view)

    def has_object_permission(self, request, view, obj):
        user = request.user
        if user and (user.is_superuser or user.is_staff):
            return True

        return IsSelf.has_object_permission(self, request, view, obj)


class IsSelfOrAdminOrReadOnly(IsSelfOrAdmin):

    """ Grant R/W to self and superusers/staff members, R/O to others. """

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True

        return IsSelfOrAdmin.has_permission(self, request, view)

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True

        return IsSelfOrAdmin.has_object_permission(self, request, view, obj)


class IsSelfOrAdminOrAuthenticatedReadOnly(IsSelfOrAdmin):

    """ Grant R/W to self and superusers/staff members, R/O to auth. """

    def has_object_permission(self, request, view, obj):
        user = request.user
        if request.method in permissions.SAFE_METHODS:
            if user.is_authenticated():
                return True

        return IsSelfOrAdmin.has_object_permission(self, request, view, obj)


class IsOwnerOrAdmin(permissions.BasePermission):
    """
    Object-level permission to only allow admin and owners of an object to edit it.
    Assumes the model instance has an `owner` attribute.
    """

    def has_object_permission(self, request, view, obj):
        if request.user is None or (not request.user.is_anonymous and not request.user.is_active):
            return False
        if request.user.is_superuser or request.user.is_staff:
            return True

        # Instance must have an attribute named `owner`.
        _request_matches = False
        if isinstance(obj, get_user_model()) and obj == request.user:
            _request_matches = True
        elif hasattr(obj, 'owner'):
            _request_matches = obj.owner == request.user
        elif hasattr(obj, 'user'):
            _request_matches = obj.user == request.user

        if not _request_matches:
            _request_matches = request.user in get_users_with_perms(obj)
        return _request_matches


class IsOwnerOrReadOnly(IsOwnerOrAdmin):
    """
    Object-level permission to only allow owners of an object to edit it.
    Assumes the model instance has an `owner` attribute.
    """

    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in permissions.SAFE_METHODS and not isinstance(obj, get_user_model()):
            return True

        return IsOwnerOrAdmin.has_object_permission(self, request, view, obj)


class IsManagerEditOrAdmin(permissions.BasePermission):
    """
    Object-level permission to only allow admin and managers to edit a group.
    """

    def has_permission(self, request, view):
        if request.method in ['POST', 'DELETE']:
            user = request.user
            return user and (user.is_superuser or user.is_staff)

        return True

    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request,
        # so we'll always allow GET, HEAD or OPTIONS requests
        if request.method in permissions.SAFE_METHODS:
            return True

        user = request.user
        if user and user.is_superuser or user.is_staff:
            return True

        is_group_manager = user and isinstance(obj, GroupProfile) and obj.user_is_role(user, "manager")
        if is_group_manager and request.method == 'PATCH':
            return True

        return False


class ResourceBasePermissionsFilter(BaseFilterBackend):
    """
    A filter backend that limits results to those where the requesting user
    has read object level permissions.
    """
    shortcut_kwargs = {
        'accept_global_perms': True,
    }

    def filter_queryset(self, request, queryset, view):
        # We want to defer this import until runtime, rather than import-time.
        # See https://github.com/encode/django-rest-framework/issues/4608
        # (Also see #1624 for why we need to make this import explicitly)

        user = request.user
        # perm_format = '%(app_label)s.view_%(model_name)s'
        # permission = self.perm_format % {
        #     'app_label': queryset.model._meta.app_label,
        #     'model_name': queryset.model._meta.model_name,
        # }

        obj_with_perms = get_resources_with_perms(user, shortcut_kwargs=self.shortcut_kwargs)
        logger.debug(f" user: {user} -- obj_with_perms: {obj_with_perms}")

        return queryset.filter(id__in=obj_with_perms.values('id'))


class UserHasPerms(DjangoModelPermissions):
    perms_map = {
        'GET': [f'base.{x}' for x in VIEW_PERMISSIONS + DOWNLOAD_PERMISSIONS],
        'POST': ['base.add_resourcebase'],
        'PUT': [f'base.{x}' for x in EDIT_PERMISSIONS + BASIC_MANAGE_PERMISSIONS],
        'PATCH': [f'base.{x}' for x in EDIT_PERMISSIONS + BASIC_MANAGE_PERMISSIONS],
        'DELETE': [f'base.{x}' for x in BASIC_MANAGE_PERMISSIONS],
    }

    def has_permission(self, request, view):
        from geonode.base.models import ResourceBase

        queryset = self._queryset(view)
        perms = self.get_required_permissions(request.method, queryset.model)

        if request.user.is_superuser:
            return True

        if view.kwargs.get('pk'):
            # if a single resource is called, we check the perms for that resource
            res = ResourceBase.objects.filter(pk=view.kwargs.get('pk')).first()
            if not res:
                raise NotFound
            general_groups = {}
            # getting the user permission for that resource
            resource_perms = list(res.get_user_perms(request.user))
            resource_groups = get_groups_with_perms(res, attach_perms=True)

            common_groups = Group.objects.filter(name__in=[groups_settings.REGISTERED_MEMBERS_GROUP_NAME, 'contributors'])\
                .filter(user=request.user)
            general_groups = {gr: list(gr.permissions.values_list('codename', flat=True)) for gr in common_groups}

            groups = {**resource_groups, **general_groups}
            # we are making this because the request.user.groups sometimes returns empty si is not fully reliable
            for group, perm in groups.items():
                # checking if the user is in that group
                if group.user_set.filter(username=request.user).exists():
                    resource_perms = list(chain(resource_perms, perm))
            # merging all available permissions into a single list
            available_perms = list(set(resource_perms))
            # fixup the permissions name
            perms_without_base = [x.replace('base.', '') for x in perms]
            # if at least one of the permissions is available the request is True
            return any([_perm in available_perms for _perm in perms_without_base])

        # check if the user have one of the perms in all the resource available
        return get_objects_for_user(request.user, perms, any_perm=True).exists()
