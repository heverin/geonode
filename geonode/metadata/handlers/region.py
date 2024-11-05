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

import logging

from rest_framework.reverse import reverse
from django.utils.translation import gettext as _

from geonode.base.models import ResourceBase
from geonode.metadata.handlers.abstract import MetadataHandler

logger = logging.getLogger(__name__)


class RegionHandler(MetadataHandler):
    """
    The RegionsHandler adds the Regions model options to the schema
    """

    def update_schema(self, jsonschema, lang=None):

        regions = {
            "type": "array",
            "title": _("Regions"),
            "description": _("keyword identifies a location"),
            "items": {
                "type": "object",
                "properties": {
                    "id": {
                        "type": "string",
                    },
                    "label": {
                        "type": "string",
                        "title": _("title")
                    },
                },
            },
            "geonode:handler": "region",
            "ui:options": {"geonode-ui:autocomplete": reverse("metadata_autocomplete_regions")},
        }

        # add regions after Attribution
        self._add_after(jsonschema, "attribution", "regions", regions)
        return jsonschema

    def get_jsonschema_instance(self, resource: ResourceBase, field_name: str, lang=None):

        return []

    def update_resource(self, resource: ResourceBase, field_name: str, json_instance: dict):

        pass

    def load_context(self, resource: ResourceBase, context: dict):

        pass
