import logging
from uuid import uuid4
import json

from django.http import JsonResponse
from django.test import RequestFactory
from django.urls import reverse

from geonode.base.models import Thesaurus, ThesaurusLabel, ThesaurusKeyword, ThesaurusKeywordLabel, ResourceBase
from django.contrib.auth import get_user_model
from geonode.tests.base import GeoNodeBaseTestSupport
import geonode.facets.views as views


logger = logging.getLogger(__name__)


class FacetsTest(GeoNodeBaseTestSupport):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.user = get_user_model().objects.create(username="user_00")
        cls.admin = get_user_model().objects.get(username="admin")

        cls._create_thesauri()
        cls._create_resources()
        cls.rf = RequestFactory()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        # remove_models(cls.get_obj_ids, type=cls.get_type, integration=cls.get_integration)

    def setUp(self):
        super().setUp()

        # self.user = get_user_model().objects.create(username="user_00")
        # self.admin = get_user_model().objects.get(username="admin")
        #
        # self.assertEqual(self.admin.username, "admin")
        # self.assertEqual(self.admin.is_superuser, True)
        #
        # self._create_thesauri()
        # self._create_resources()
        # self.rf = RequestFactory()

    @classmethod
    def _create_thesauri(cls):
        cls.thesauri = {}
        cls.thesauri_k = {}

        for tn in range(2):
            t = Thesaurus.objects.create(identifier=f"t_{tn}", title=f"Thesaurus {tn}")
            cls.thesauri[tn] = t
            for tl in (
                "en",
                "it",
            ):
                ThesaurusLabel.objects.create(thesaurus=t, lang=tl, label=f"TLabel {tn} {tl}")

            for tkn in range(10):
                tk = ThesaurusKeyword.objects.create(thesaurus=t, alt_label=f"alt_tkn{tkn}_t{tn}")
                cls.thesauri_k[f"{tn}_{tkn}"] = tk
                for tkl in (
                    "en",
                    "it",
                ):
                    ThesaurusKeywordLabel.objects.create(keyword=tk, lang=tkl, label=f"T{tn}_K{tkn}_{tkl}")

    @classmethod
    def _create_resources(self):
        public_perm_spec = {"users": {"AnonymousUser": ["view_resourcebase"]}, "groups": []}

        for x in range(20):
            d: ResourceBase = ResourceBase.objects.create(
                title=f"dataset_{x:02}",
                uuid=str(uuid4()),
                owner=self.user,
                abstract=f"Abstract for dataset {x:02}",
                subtype="vector",
                is_approved=True,
                is_published=True,
            )

            # These are the assigned keywords to the Resources

            # RB00 ->            T1K0
            # RB01 ->  T0K0      T1K0
            # RB02 ->            T1K0
            # RB03 ->  T0K0      T1K0
            # RB04 ->            T1K0
            # RB05 ->  T0K0      T1K0
            # RB06 ->            T1K0
            # RB07 ->  T0K0      T1K0
            # RB08 ->            T1K0
            # RB09 ->  T0K0      T1K0
            # RB10 ->
            # RB11 ->  T0K0 T0K1
            # RB12 ->
            # RB13 ->  T0K0 T0K1
            # RB14 ->
            # RB15 ->  T0K0 T0K1
            # RB16 ->
            # RB17 ->  T0K0 T0K1
            # RB18 ->
            # RB19 ->  T0K0 T0K1

            if x % 2 == 1:
                print(f"ADDING KEYWORDS {self.thesauri_k['0_0']} to RB {d}")
                d.tkeywords.add(self.thesauri_k["0_0"])
                d.save()
            if x % 2 == 1 and x > 10:
                print(f"ADDING KEYWORDS {self.thesauri_k['0_1']} to RB {d}")
                d.tkeywords.add(self.thesauri_k["0_1"])
                d.save()
            if x < 10:
                print(f"ADDING KEYWORDS {self.thesauri_k['1_0']} to RB {d}")
                d.tkeywords.add(self.thesauri_k["1_0"])
                d.save()

            d.set_permissions(public_perm_spec)

    @staticmethod
    def _facets_to_map(facets):
        return {f["name"]: f for f in facets}

    def test_facets_base(self):
        req = self.rf.get(reverse("list_facets"), data={"lang": "en"})
        res: JsonResponse = views.list_facets(req)
        obj = json.loads(res.content)
        self.assertIn("facets", obj)
        facets_list = obj["facets"]
        self.assertEqual(4, len(facets_list))
        fmap = self._facets_to_map(facets_list)
        for name in ("category", "owner", "t_0", "t_1"):
            self.assertIn(name, fmap)

    def test_facets_rich(self):
        # make sure the resources are in
        c = ResourceBase.objects.count()
        self.assertEqual(20, c)

        # make sure tkeywords have been assigned by checking a sample resource
        rb = ResourceBase.objects.get(title="dataset_01")
        self.assertEqual(2, rb.tkeywords.count())

        # run the request
        req = self.rf.get(reverse("list_facets"), data={"include_topics": 1, "lang": "en"})
        res: JsonResponse = views.list_facets(req)
        obj = json.loads(res.content)

        facets_list = obj["facets"]
        self.assertEqual(4, len(facets_list))
        fmap = self._facets_to_map(facets_list)
        for expected in (
            {
                "name": "category",
                "topics": {
                    "total": 1,
                },
            },
            {
                "name": "owner",
                "topics": {
                    "total": 1,
                },
            },
            {
                "name": "t_0",
                "topics": {
                    "total": 2,
                    "items": {
                        "T0_K0_en": {"label": "T0_K0_en", "count": 10},
                        "T0_K1_en": {"label": "T0_K1_en", "count": 5},
                    },
                },
            },
            {
                "name": "t_1",
                "topics": {
                    "total": 1,
                    "items": {
                        "T1_K0_en": {"count": 10},
                    },
                },
            },
        ):
            name = expected["name"]
            self.assertIn(name, fmap)
            facet = fmap[name]
            expected_topics = expected["topics"]
            for topic_key in expected_topics:
                if topic_key != "items":
                    self.assertEqual(
                        expected_topics[topic_key], facet["topics"][topic_key], f"Mismatching '{topic_key}'"
                    )
                else:
                    items = facet["topics"]["items"]
                    expected_items = expected_topics["items"]
                    for item in items:
                        self.assertIn(item["label"], expected_items, f"topic not found '{item['label']}'")
                        x_item = expected_items[item["label"]]
                        for _k, _v in x_item.items():
                            self.assertEqual(_v, item[_k], f"Mismatch item key:{_k}")

        # print(json.dumps(json.loads(res.content), indent=True))

    def test_bad_lang(self):
        # for thesauri, make sure that by requesting a non-existent language the faceting is still working,
        # using the default labels
        # TODO impl+test
        pass

    def test_user_auth(self):
        # make sure the user authorization pre-filters the visible resources
        # TODO test
        pass

    def test_thesauri_reloading(self):
        # Thesauri facets are cached.
        # Make sure that when Thesauri or ThesauriLabel change the facets cache is invalidated
        # TODO impl+test
        pass
