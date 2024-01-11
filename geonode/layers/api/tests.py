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
from io import BytesIO
import logging

from unittest.mock import patch
from django.contrib.auth import get_user_model
from urllib.parse import urljoin

from django.conf import settings
from django.urls import reverse
from rest_framework.test import APITestCase

from guardian.shortcuts import assign_perm, get_anonymous_user
from geonode.geoserver.createlayer.utils import create_dataset

from geonode.base.models import Link
from geonode.base.populate_test_data import create_models, create_single_dataset
from geonode.layers.models import Attribute, Dataset
from geonode.maps.models import Map, MapLayer

logger = logging.getLogger(__name__)


class DatasetsApiTests(APITestCase):
    fixtures = ["initial_data.json", "group_test_data.json", "default_oauth_apps.json"]

    def setUp(self):
        self.exml_path = f"{settings.PROJECT_ROOT}/base/fixtures/test_xml.xml"
        create_models(b"document")
        create_models(b"map")
        create_models(b"dataset")

    def test_datasets(self):
        """
        Ensure we can access the Layers list.
        """
        url = reverse("datasets-list")
        # Anonymous
        response = self.client.get(url, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 5)
        self.assertEqual(response.data["total"], 8)

        # Pagination
        self.assertEqual(len(response.data["datasets"]), 8)
        logger.debug(response.data)

        for _l in response.data["datasets"]:
            self.assertTrue(_l["resource_type"], "dataset")
        # Test list response doesn't have attribute_set
        self.assertIsNotNone(response.data["datasets"][0].get("ptype"))
        self.assertIsNone(response.data["datasets"][0].get("attribute_set"))
        self.assertIsNone(response.data["datasets"][0].get("featureinfo_custom_template"))

        _dataset = Dataset.objects.first()
        assign_perm("base.view_resourcebase", get_anonymous_user(), _dataset.get_self_resource())

        # Test detail response has attribute_set
        url = urljoin(f"{reverse('datasets-list')}/", f"{_dataset.pk}")
        response = self.client.get(url, format="json")
        self.assertIsNotNone(response.data["dataset"].get("ptype"))
        self.assertIsNotNone(response.data["dataset"].get("subtype"))
        self.assertIsNotNone(response.data["dataset"].get("attribute_set"))

        # Test "featureinfo_custom_template"
        _attribute, _ = Attribute.objects.get_or_create(dataset=_dataset, attribute="name")
        try:
            _attribute.visible = True
            _attribute.attribute_type = Attribute.TYPE_PROPERTY
            _attribute.description = "The Name"
            _attribute.attribute_label = "Name"
            _attribute.display_order = 1
            _attribute.save()

            url = urljoin(f"{reverse('datasets-list')}/", f"{_dataset.pk}")
            response = self.client.get(url, format="json")
            self.assertIsNotNone(response.data["dataset"].get("featureinfo_custom_template"))
            self.assertEqual(
                response.data["dataset"].get("featureinfo_custom_template"),
                '<div style="overflow-x:hidden"><div class="row"><div class="col-xs-6" style="font-weight: bold; word-wrap: break-word;">Name:</div>\
                             <div class="col-xs-6" style="word-wrap: break-word;">${properties[\'name\']}</div></div></div>',
            )

            _dataset.featureinfo_custom_template = "<div>Foo Bar</div>"
            _dataset.save()
            url = urljoin(f"{reverse('datasets-list')}/", f"{_dataset.pk}")
            response = self.client.get(url, format="json")
            self.assertIsNotNone(response.data["dataset"].get("featureinfo_custom_template"))
            self.assertEqual(
                response.data["dataset"].get("featureinfo_custom_template"),
                '<div style="overflow-x:hidden"><div class="row"><div class="col-xs-6" style="font-weight: bold; word-wrap: break-word;">Name:</div>\
                             <div class="col-xs-6" style="word-wrap: break-word;">${properties[\'name\']}</div></div></div>',
            )

            _dataset.use_featureinfo_custom_template = True
            _dataset.save()
            url = urljoin(f"{reverse('datasets-list')}/", f"{_dataset.pk}")
            response = self.client.get(url, format="json")
            self.assertIsNotNone(response.data["dataset"].get("featureinfo_custom_template"))
            self.assertEqual(response.data["dataset"].get("featureinfo_custom_template"), "<div>Foo Bar</div>")
        finally:
            _attribute.delete()
            _dataset.featureinfo_custom_template = None
            _dataset.use_featureinfo_custom_template = False
            _dataset.save()

    def test_extra_metadata_included_with_param(self):
        _dataset = Dataset.objects.first()
        url = urljoin(f"{reverse('datasets-list')}/", f"{_dataset.pk}")
        data = {"include[]": "metadata"}

        response = self.client.get(url, format="json", data=data)
        self.assertIsNotNone(response.data["dataset"].get("metadata"))

        response = self.client.get(url, format="json")
        self.assertNotIn("metadata", response.data["dataset"])

    def test_get_dataset_related_maps_and_maplayers(self):
        dataset = Dataset.objects.first()
        assign_perm("base.view_resourcebase", get_anonymous_user(), dataset.get_self_resource())

        url = reverse("datasets-detail", kwargs={"pk": dataset.pk})
        response = self.client.get(f"{url}/maplayers", format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 0)

        response = self.client.get(f"{url}/maplayers", format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 0)

        response = self.client.get(f"{url}/maps", format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 0)
        map = Map.objects.first()
        map_layer = MapLayer.objects.create(
            map=map,
            extra_params={},
            name=dataset.alternate,
            store=None,
            current_style=None,
            ows_url=None,
            local=True,
            dataset=dataset,
        )
        response = self.client.get(f"{url}/maplayers", format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)
        self.assertEqual(response.json()[0]["pk"], map_layer.pk)

        response = self.client.get(f"{url}/maps", format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)
        self.assertEqual(response.json()[0]["pk"], map.pk)

    def test_raw_HTML_stripped_properties(self):
        """
        Ensure "raw_*" properties returns no HTML or carriage-return tag
        """
        dataset = Dataset.objects.first()
        dataset.abstract = (
            '<p><em>No abstract provided</em>.</p>\r\n<p><img src="data:image/jpeg;base64,/9j/4AAQSkZJR/>'
        )
        dataset.constraints_other = '<p><span style="text-decoration: underline;">None</span></p>'
        dataset.supplemental_information = "<p>No information provided &iacute;</p> <p>&pound;682m</p>"
        dataset.data_quality_statement = '<p><strong>OK</strong></p>\r\n<table style="border-collapse: collapse; width:\
            85.2071%;" border="1">\r\n<tbody>\r\n<tr>\r\n<td style="width: 49.6528%;">1</td>\r\n<td style="width:\
            50%;">2</td>\r\n</tr>\r\n<tr>\r\n<td style="width: 49.6528%;">a</td>\r\n<td style="width: 50%;">b</td>\
            \r\n</tr>\r\n</tbody>\r\n</table>'
        dataset.save()

        # Admin
        self.assertTrue(self.client.login(username="admin", password="admin"))

        url = reverse("datasets-detail", kwargs={"pk": dataset.pk})
        response = self.client.get(url, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(int(response.data["dataset"]["pk"]), int(dataset.pk))
        self.assertEqual(response.data["dataset"]["raw_abstract"], "No abstract provided.")
        self.assertEqual(response.data["dataset"]["raw_constraints_other"], "None")
        self.assertEqual(response.data["dataset"]["raw_supplemental_information"], "No information provided í £682m")
        self.assertEqual(response.data["dataset"]["raw_data_quality_statement"], "OK    1 2   a b")

    def test_layer_replace_anonymous_should_raise_error(self):
        layer = Dataset.objects.first()
        url = reverse("datasets-replace-dataset", args=(layer.id,))

        expected = {
            "success": False,
            "errors": ["Authentication credentials were not provided."],
            "code": "not_authenticated",
        }

        response = self.client.patch(url)
        self.assertEqual(403, response.status_code)
        self.assertDictEqual(expected, response.json())

    def test_layer_replace_should_redirect_for_not_accepted_method(self):
        layer = Dataset.objects.first()
        url = reverse("datasets-replace-dataset", args=(layer.id,))
        self.client.login(username="admin", password="admin")

        response = self.client.post(url)
        self.assertEqual(405, response.status_code)

        response = self.client.get(url)
        self.assertEqual(405, response.status_code)

    def test_layer_replace_should_raise_error_if_layer_does_not_exists(self):
        url = reverse("datasets-replace-dataset", args=(999999999999999,))

        expected = {"success": False, "errors": ["Layer with ID 999999999999999 is not available"], "code": "not_found"}

        self.client.login(username="admin", password="admin")

        response = self.client.patch(url)
        self.assertEqual(404, response.status_code)
        self.assertDictEqual(expected, response.json())

    def test_dataset_append_anonymous_should_raise_error(self):
        layer = Dataset.objects.first()
        url = reverse("datasets-append-dataset", args=(layer.id,))

        expected = {
            "success": False,
            "errors": ["Authentication credentials were not provided."],
            "code": "not_authenticated",
        }

        response = self.client.patch(url)
        self.assertEqual(403, response.status_code)
        self.assertDictEqual(expected, response.json())

    def test_dataset_append_should_redirect_for_not_accepted_method(self):
        layer = Dataset.objects.first()
        url = reverse("datasets-append-dataset", args=(layer.id,))
        self.client.login(username="admin", password="admin")

        response = self.client.post(url)
        self.assertEqual(405, response.status_code)

        response = self.client.get(url)
        self.assertEqual(405, response.status_code)

    def test_dataset_append_should_raise_error_if_layer_does_not_exists(self):
        url = reverse("datasets-append-dataset", args=(999999999999999,))

        expected = {"success": False, "errors": ["Layer with ID 999999999999999 is not available"], "code": "not_found"}

        self.client.login(username="admin", password="admin")

        response = self.client.patch(url)
        self.assertEqual(404, response.status_code, response.json())
        self.assertDictEqual(expected, response.json())

    @patch("geonode.layers.api.views.validate_input_source")
    def test_layer_replace_should_work(self, _validate_input_source):
        _validate_input_source.return_value = True

        admin = get_user_model().objects.get(username="admin")

        if Dataset.objects.filter(name="single_point").exists():
            """
            If the dataset already exists in the test env, we dont want that the test fail
            so we rename it and then we will rollback the cnahge
            """
            _dataset = Dataset.objects.get(name="single_point")
            _dataset.name = "single_point_2"
            _dataset.save()

        try:
            layer = create_dataset(
                "single_point",
                "single_point",
                admin,
                "Point",
            )
        except Exception as e:
            if "There is already a layer named" not in e.args[0]:
                raise e
            else:
                layer = create_single_dataset("single_point")

        cnt = Dataset.objects.count()

        layer.refresh_from_db()
        logger.error(layer.alternate)
        # renaming the file in the same way as the lasyer name
        # the filename must be consiste with the layer name

        github_path = "https://github.com/GeoNode/gisdata/tree/master/gisdata/data/good/vector/"
        payload = {
            "store_spatial_files": False,
            "base_file": f"{github_path}/single_point.shp",
            "dbf_file": f"{github_path}/single_point.dbf",
            "shx_file": f"{github_path}/single_point.shx",
            "prj_file": f"{github_path}/single_point.prj",
        }

        url = reverse("datasets-replace-dataset", args=(layer.id,))

        self.client.login(username="admin", password="admin")

        response = self.client.patch(url, data=payload)
        self.assertEqual(200, response.status_code, response.json())

        layer.refresh_from_db()
        # evaluate that the number of available layer is not changed
        self.assertEqual(Dataset.objects.count(), cnt)

    def test_patch_point_of_contact(self):
        layer = Dataset.objects.first()
        url = urljoin(f"{reverse('datasets-list')}/", f"{layer.id}")
        self.client.login(username="admin", password="admin")
        get_user_model().objects.get_or_create(username="ninja")
        get_user_model().objects.get_or_create(username="turtle")
        users = get_user_model().objects.exclude(pk=-1)
        user_ids = [user.pk for user in users]
        patch_data = {"poc": [{"pk": uid} for uid in user_ids]}
        response = self.client.patch(url, data=patch_data, format="json")
        self.assertEqual(200, response.status_code)
        self.assertTrue(
            all(user_id in [poc.get("pk") for poc in response.json().get("dataset").get("poc")] for user_id in user_ids)
        )
        # Resetting all point of contact
        response = self.client.patch(url, data={"poc": []}, format="json")
        self.assertEqual(200, response.status_code)
        self.assertTrue(
            all(
                user_id not in [poc.get("pk") for poc in response.json().get("dataset").get("poc")]
                for user_id in user_ids
            )
        )

    def test_patch_metadata_author(self):
        layer = Dataset.objects.first()
        url = urljoin(f"{reverse('datasets-list')}/", f"{layer.id}")
        self.client.login(username="admin", password="admin")
        get_user_model().objects.get_or_create(username="ninja")
        get_user_model().objects.get_or_create(username="turtle")
        users = get_user_model().objects.exclude(pk=-1)
        user_ids = [user.pk for user in users]
        patch_data = {"metadata_author": [{"pk": uid} for uid in user_ids]}
        response = self.client.patch(url, data=patch_data, format="json")
        self.assertEqual(200, response.status_code)
        self.assertTrue(
            all(
                user_id
                in [
                    metadata_author.get("pk")
                    for metadata_author in response.json().get("dataset").get("metadata_author")
                ]
                for user_id in user_ids
            )
        )
        # Resetting all metadata authors
        response = self.client.patch(url, data={"metadata_author": []}, format="json")
        self.assertEqual(200, response.status_code)
        self.assertTrue(
            all(
                user_id
                not in [
                    metadata_author.get("pk")
                    for metadata_author in response.json().get("dataset").get("metadata_author")
                ]
                for user_id in user_ids
            )
        )

    def test_patch_processor(self):
        layer = Dataset.objects.first()
        url = urljoin(f"{reverse('datasets-list')}/", f"{layer.id}")
        self.client.login(username="admin", password="admin")
        get_user_model().objects.get_or_create(username="ninja")
        get_user_model().objects.get_or_create(username="turtle")
        users = get_user_model().objects.exclude(pk=-1)
        user_ids = [user.pk for user in users]
        patch_data = {"processor": [{"pk": uid} for uid in user_ids]}
        response = self.client.patch(url, data=patch_data, format="json")
        self.assertEqual(200, response.status_code)
        self.assertTrue(
            all(
                user_id in [processor.get("pk") for processor in response.json().get("dataset").get("processor")]
                for user_id in user_ids
            )
        )
        # Resetting all processors
        response = self.client.patch(url, data={"processor": []}, format="json")
        self.assertEqual(200, response.status_code)
        self.assertTrue(
            all(
                user_id not in [processor.get("pk") for processor in response.json().get("dataset").get("processor")]
                for user_id in user_ids
            )
        )

    def test_patch_publisher(self):
        layer = Dataset.objects.first()
        url = urljoin(f"{reverse('datasets-list')}/", f"{layer.id}")
        self.client.login(username="admin", password="admin")
        get_user_model().objects.get_or_create(username="ninja")
        get_user_model().objects.get_or_create(username="turtle")
        users = get_user_model().objects.exclude(pk=-1)
        user_ids = [user.pk for user in users]
        patch_data = {"publisher": [{"pk": uid} for uid in user_ids]}
        response = self.client.patch(url, data=patch_data, format="json")
        self.assertEqual(200, response.status_code)
        self.assertTrue(
            all(
                user_id in [publisher.get("pk") for publisher in response.json().get("dataset").get("publisher")]
                for user_id in user_ids
            )
        )
        # Resetting all publishers
        response = self.client.patch(url, data={"publisher": []}, format="json")
        self.assertEqual(200, response.status_code)
        self.assertTrue(
            all(
                user_id not in [publisher.get("pk") for publisher in response.json().get("dataset").get("publisher")]
                for user_id in user_ids
            )
        )

    def test_patch_custodian(self):
        layer = Dataset.objects.first()
        url = urljoin(f"{reverse('datasets-list')}/", f"{layer.id}")
        self.client.login(username="admin", password="admin")
        get_user_model().objects.get_or_create(username="ninja")
        get_user_model().objects.get_or_create(username="turtle")
        users = get_user_model().objects.exclude(pk=-1)
        user_ids = [user.pk for user in users]
        patch_data = {"custodian": [{"pk": uid} for uid in user_ids]}
        response = self.client.patch(url, data=patch_data, format="json")
        self.assertEqual(200, response.status_code)
        self.assertTrue(
            all(
                user_id in [custodian.get("pk") for custodian in response.json().get("dataset").get("custodian")]
                for user_id in user_ids
            )
        )
        # Resetting all custodians
        response = self.client.patch(url, data={"custodian": []}, format="json")
        self.assertEqual(200, response.status_code)
        self.assertTrue(
            all(
                user_id not in [custodian.get("pk") for custodian in response.json().get("dataset").get("custodian")]
                for user_id in user_ids
            )
        )

    def test_patch_distributor(self):
        layer = Dataset.objects.first()
        url = urljoin(f"{reverse('datasets-list')}/", f"{layer.id}")
        self.client.login(username="admin", password="admin")
        get_user_model().objects.get_or_create(username="ninja")
        get_user_model().objects.get_or_create(username="turtle")
        users = get_user_model().objects.exclude(pk=-1)
        user_ids = [user.pk for user in users]
        patch_data = {"distributor": [{"pk": uid} for uid in user_ids]}
        response = self.client.patch(url, data=patch_data, format="json")
        self.assertEqual(200, response.status_code)
        self.assertTrue(
            all(
                user_id in [distributor.get("pk") for distributor in response.json().get("dataset").get("distributor")]
                for user_id in user_ids
            )
        )
        # Resetting all distributers
        response = self.client.patch(url, data={"distributor": []}, format="json")

        self.assertEqual(200, response.status_code)
        self.assertTrue(
            all(
                user_id
                not in [distributor.get("pk") for distributor in response.json().get("dataset").get("distributor")]
                for user_id in user_ids
            )
        )

    def test_patch_resource_user(self):
        layer = Dataset.objects.first()
        url = urljoin(f"{reverse('datasets-list')}/", f"{layer.id}")
        self.client.login(username="admin", password="admin")
        get_user_model().objects.get_or_create(username="ninja")
        get_user_model().objects.get_or_create(username="turtle")
        users = get_user_model().objects.exclude(pk=-1)
        user_ids = [user.pk for user in users]
        patch_data = {"resource_user": [{"pk": uid} for uid in user_ids]}
        response = self.client.patch(url, data=patch_data, format="json")
        self.assertEqual(200, response.status_code)
        self.assertTrue(
            all(
                user_id
                in [resource_user.get("pk") for resource_user in response.json().get("dataset").get("resource_user")]
                for user_id in user_ids
            )
        )
        # Resetting all resource users
        response = self.client.patch(url, data={"resource_user": []}, format="json")
        self.assertEqual(200, response.status_code)
        self.assertTrue(
            all(
                user_id
                not in [
                    resource_user.get("pk") for resource_user in response.json().get("dataset").get("resource_user")
                ]
                for user_id in user_ids
            )
        )

    def test_patch_resource_provider(self):
        layer = Dataset.objects.first()
        url = urljoin(f"{reverse('datasets-list')}/", f"{layer.id}")
        self.client.login(username="admin", password="admin")
        get_user_model().objects.get_or_create(username="ninja")
        get_user_model().objects.get_or_create(username="turtle")
        users = get_user_model().objects.exclude(pk=-1)
        user_ids = [user.pk for user in users]
        patch_data = {"resource_provider": [{"pk": uid} for uid in user_ids]}
        response = self.client.patch(url, data=patch_data, format="json")
        self.assertEqual(200, response.status_code)
        self.assertTrue(
            all(
                user_id
                in [
                    resource_provider.get("pk")
                    for resource_provider in response.json().get("dataset").get("resource_provider")
                ]
                for user_id in user_ids
            )
        )
        # Resetting all principal investigator
        response = self.client.patch(url, data={"resource_provider": []}, format="json")
        self.assertEqual(200, response.status_code)
        self.assertTrue(
            all(
                user_id
                not in [
                    resource_provider.get("pk")
                    for resource_provider in response.json().get("dataset").get("resource_provider")
                ]
                for user_id in user_ids
            )
        )

    def test_patch_originator(self):
        layer = Dataset.objects.first()
        url = urljoin(f"{reverse('datasets-list')}/", f"{layer.id}")
        self.client.login(username="admin", password="admin")

        get_user_model().objects.get_or_create(username="ninja")
        get_user_model().objects.get_or_create(username="turtle")
        users = get_user_model().objects.exclude(pk=-1)
        user_ids = [user.pk for user in users]
        patch_data = {"originator": [{"pk": uid} for uid in user_ids]}
        response = self.client.patch(url, data=patch_data, format="json")
        self.assertEqual(200, response.status_code)
        self.assertTrue(
            all(
                user_id in [originator.get("pk") for originator in response.json().get("dataset").get("originator")]
                for user_id in user_ids
            )
        )
        # Resetting all originators
        response = self.client.patch(url, data={"originator": []}, format="json")
        self.assertEqual(200, response.status_code)
        self.assertTrue(
            all(
                user_id not in [originator.get("pk") for originator in response.json().get("dataset").get("originator")]
                for user_id in user_ids
            )
        )

    def test_patch_principal_investigator(self):
        layer = Dataset.objects.first()
        url = urljoin(f"{reverse('datasets-list')}/", f"{layer.id}")
        self.client.login(username="admin", password="admin")
        get_user_model().objects.get_or_create(username="ninja")
        get_user_model().objects.get_or_create(username="turtle")
        users = get_user_model().objects.exclude(pk=-1)
        user_ids = [user.pk for user in users]
        patch_data = {"principal_investigator": [{"pk": uid} for uid in user_ids]}
        response = self.client.patch(url, data=patch_data, format="json")
        self.assertEqual(200, response.status_code)
        self.assertTrue(
            all(
                user_id
                in [
                    principal_investigator.get("pk")
                    for principal_investigator in response.json().get("dataset").get("principal_investigator")
                ]
                for user_id in user_ids
            )
        )
        # Resetting all principal investigator
        response = self.client.patch(url, data={"principal_investigator": []}, format="json")
        self.assertEqual(200, response.status_code)
        self.assertTrue(
            all(
                user_id
                not in [
                    principal_investigator.get("pk")
                    for principal_investigator in response.json().get("dataset").get("principal_investigator")
                ]
                for user_id in user_ids
            )
        )

    def test_metadata_update_for_not_supported_method(self):
        layer = Dataset.objects.first()
        url = reverse("datasets-replace-metadata", args=(layer.id,))
        self.client.login(username="admin", password="admin")

        response = self.client.post(url)
        self.assertEqual(405, response.status_code)

        response = self.client.get(url)
        self.assertEqual(405, response.status_code)

    def test_metadata_update_for_not_authorized_user(self):
        layer = Dataset.objects.first()
        url = reverse("datasets-replace-metadata", args=(layer.id,))

        response = self.client.put(url)
        self.assertEqual(403, response.status_code)

    def test_unsupported_file_throws_error(self):
        layer = Dataset.objects.first()
        url = reverse("datasets-replace-metadata", args=(layer.id,))
        self.client.login(username="admin", password="admin")

        data = '<?xml version="1.0" encoding="UTF-8"?><invalid></invalid>'
        f = BytesIO(bytes(data, encoding="utf-8"))
        f.name = "metadata.xml"
        put_data = {"metadata_file": f}
        response = self.client.put(url, data=put_data)
        self.assertEqual(500, response.status_code)

    def test_valid_metadata_file_with_different_uuid(self):
        layer = Dataset.objects.first()
        url = reverse("datasets-replace-metadata", args=(layer.id,))
        self.client.login(username="admin", password="admin")

        f = open(self.exml_path, "r")
        put_data = {"metadata_file": f}
        response = self.client.put(url, data=put_data)
        self.assertEqual(500, response.status_code)

    def test_permissions_for_not_permitted_user(self):
        get_user_model().objects.create_user(
            username="some_user",
            password="some_password",
            email="some_user@geonode.org",
        )
        layer = Dataset.objects.first()
        url = reverse("datasets-replace-metadata", args=(layer.id,))
        self.client.login(username="some_user", password="some_password")

        uuid = layer.uuid
        data = open(self.exml_path).read()
        data = data.replace("7cfbc42c-efa7-431c-8daa-1399dff4cd19", uuid)
        f = BytesIO(bytes(data, encoding="utf-8"))
        f.name = "metadata.xml"
        put_data = {"metadata_file": f}
        response = self.client.put(url, data=put_data)
        self.assertEqual(403, response.status_code)

    def test_permissions_for_permitted_user(self):
        another_non_admin_user = get_user_model().objects.create_user(
            username="some_other_user",
            password="some_other_password",
            email="some_other_user@geonode.org",
        )
        layer = Dataset.objects.first()
        assign_perm("base.change_resourcebase_metadata", another_non_admin_user, layer.get_self_resource())
        url = reverse("datasets-replace-metadata", args=(layer.id,))
        self.client.login(username="some_other_user", password="some_other_password")

        uuid = layer.uuid
        data = open(self.exml_path).read()
        data = data.replace("7cfbc42c-efa7-431c-8daa-1399dff4cd19", uuid)
        f = BytesIO(bytes(data, encoding="utf-8"))
        f.name = "metadata.xml"
        put_data = {"metadata_file": f}
        response = self.client.put(url, data=put_data)
        self.assertEqual(200, response.status_code)

    def test_valid_metadata_file(self):
        layer = Dataset.objects.first()
        url = reverse("datasets-replace-metadata", args=(layer.id,))
        self.client.login(username="admin", password="admin")

        uuid = layer.uuid
        data = open(self.exml_path).read()
        data = data.replace("7cfbc42c-efa7-431c-8daa-1399dff4cd19", uuid)
        f = BytesIO(bytes(data, encoding="utf-8"))
        f.name = "metadata.xml"
        put_data = {"metadata_file": f}
        response = self.client.put(url, data=put_data)
        self.assertEqual(200, response.status_code)

    def test_download_api(self):
        dataset = create_single_dataset("test_dataset")
        url = reverse("datasets-detail", kwargs={"pk": dataset.pk})
        response = self.client.get(url)
        self.assertTrue(response.status_code == 200)
        data = response.json()["dataset"]
        download_url_data = data["download_urls"][0]
        download_url = reverse("dataset_download", args=[dataset.alternate])
        self.assertEqual(download_url_data["default"], True)
        self.assertEqual(download_url_data["ajax_safe"], True)
        self.assertEqual(download_url_data["url"], download_url)

        link = Link(link_type="original", url="https://myoriginal.org", resource=dataset)
        link.save()

        response = self.client.get(url)
        data = response.json()["dataset"]
        download_url_data = data["download_urls"][0]
        download_url = reverse("dataset_download", args=[dataset.alternate])
        self.assertEqual(download_url_data["default"], True)
        self.assertEqual(download_url_data["ajax_safe"], False)
        self.assertEqual(download_url_data["url"], "https://myoriginal.org")
