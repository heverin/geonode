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
from abc import ABCMeta, abstractmethod
from geonode.base.models import ResourceBase

logger = logging.getLogger(__name__)


class MetadataHandler(metaclass=ABCMeta):
    """
    Handlers take care of reading, storing, encoding,
    decoding subschemas of the main Resource
    """

    @abstractmethod
    def update_schema(self, jsonschema: dict, lang=None):
        """
        It is called by the MetadataManager when creating the JSON Schema
        It adds the subschema handled by the handler, and returns the
        augmented instance of the JSON Schema.
        """
        pass

    @abstractmethod
    def get_jsonschema_instance(self, resource: ResourceBase, field_name: str, context: dict, lang: str = None):
        """
        Called when reading metadata, returns the instance of the sub-schema
        associated with the field field_name.
        """
        pass

    @abstractmethod
    def update_resource(self, resource: ResourceBase, field_name: str, json_instance: dict, errors: list, **kwargs):
        """
        Called when persisting data, updates the field field_name of the resource
        with the content content, where json_instance is  the full JSON Schema instance,
        in case the handler needs some cross related data contained in the resource.
        """
        pass

    def load_serialization_context(self, resource: ResourceBase, jsonschema: dict, context: dict):
        """
        Called before calls to get_jsonschema_instance in order to initialize info needed by the handler
        """
        pass

    def load_deserialization_context(self, resource: ResourceBase, context: dict):
        """
        Called before calls to update_resource in order to initialize info needed by the handler
        """
        pass

    def _add_after(self, jsonschema, after_what, property_name, subschema):
        # add thesauri after category
        ret_properties = {}
        added = False
        for key, val in jsonschema["properties"].items():
            ret_properties[key] = val
            if key == after_what:
                ret_properties[property_name] = subschema
                added = True

        if not added:
            logger.warning(f'Could not add "{property_name}" after "{after_what}"')
            ret_properties[property_name] = subschema

        jsonschema["properties"] = ret_properties

    @staticmethod
    def _set_error(errors: dict, path: list, msg: str):
        elem = errors
        for step in path:
            elem = elem.setdefault(step, {})
        elem = elem.setdefault("__errors", [])
        elem.append(msg)
