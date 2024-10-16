#########################################################################
#
# Copyright (C) 2024 OSGeo
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
from rest_framework import serializers
from dynamic_rest.serializers import DynamicModelSerializer

from geonode.base.models import ResourceBase


class MetadataFileSerializer(DynamicModelSerializer):
    class Meta:
        ref_name = "MetadataFileSerializer"
        model = ResourceBase
        view_name = "importer_upload"
        fields = ("overwrite_existing_layer", "resource_pk", "base_file", "source")

    base_file = serializers.FileField()
    overwrite_existing_layer = serializers.BooleanField(required=False, default=True)
    resource_pk = serializers.CharField(required=True)
    source = serializers.CharField(required=False, default="resource_file_upload")