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
from django.urls import path
from rest_framework import routers

from geonode.metadata.api import views
from geonode.metadata.api.views import ProfileAutocomplete

router = routers.DefaultRouter()
router.register(r"metadata", views.MetadataViewSet, basename="metadata")

urlpatterns = router.urls + [
    path(
        r"metadata/autocomplete/thesaurus/<thesaurusid>)/keywords",
        views.tkeywords_autocomplete,
        name="metadata_autocomplete_tkeywords",
    ),
    path(r"metadata/autocomplete/users", ProfileAutocomplete.as_view(), name="metadata_autocomplete_users"),
    # path(r"metadata/autocomplete/users", login_required(ProfileAutocomplete.as_view()), name="metadata_autocomplete_users"),
]
