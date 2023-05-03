#########################################################################
#
# Copyright (C) 2023 OSGeo
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

from django.apps import AppConfig

from geonode.facets.models import FacetProvider
from geonode.facets.providers.category import CategoryFacetProvider

logger = logging.getLogger(__name__)

registered_facets = dict()


class GeoNodeFacetsConfig(AppConfig):
    name = "geonode.facets"
    verbose_name = "GeoNode Facets endpoints"

    def ready(self):
        from geonode.urls import urlpatterns
        from . import urls

        urlpatterns += urls.urlpatterns

        init_providers()


def init_providers():
    from geonode.facets.providers.thesaurus import create_thesaurus_providers
    from geonode.facets.providers.users import OwnerFacetProvider

    register_facet_provider(CategoryFacetProvider())
    register_facet_provider(OwnerFacetProvider())

    # Thesaurus providers initialiazion should be called at startup and whenever records in Thesaurus or ThesaurusLabel change
    for provider in create_thesaurus_providers():
        register_facet_provider(provider)


def register_facet_provider(provider: FacetProvider):
    logging.info(f"Registering {provider}")
    registered_facets[provider.get_info()["name"]] = provider
