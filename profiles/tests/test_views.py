import json
from unittest.mock import patch
from django.test import TestCase, Client
from profiles.models import Profile


class ProfilesApiTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.profile_a = Profile.objects.create(
            name="maria",
            gender="female",
            gender_probability=0.92,
            age=24,
            age_group="adult",
            country_id="NG",
            country_name="Nigeria",
            country_probability=0.91,
        )
        cls.profile_b = Profile.objects.create(
            name="joseph",
            gender="male",
            gender_probability=0.88,
            age=19,
            age_group="teenager",
            country_id="KE",
            country_name="Kenya",
            country_probability=0.83,
        )
        cls.profile_c = Profile.objects.create(
            name="ade",
            gender="male",
            gender_probability=0.96,
            age=33,
            age_group="adult",
            country_id="NG",
            country_name="Nigeria",
            country_probability=0.89,
        )

    def setUp(self):
        self.client = Client()
        self.ensure_seed_patcher = patch("profiles.views.ensure_seed", return_value=None)
        self.ensure_seed_patcher.start()

    def tearDown(self):
        self.ensure_seed_patcher.stop()

    def test_get_profiles_success(self):
        response = self.client.get("/api/profiles")
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["page"], 1)
        self.assertEqual(data["limit"], 10)
        self.assertEqual(data["total"], 3)
        self.assertEqual(len(data["data"]), 3)

    def test_get_profiles_filter_by_gender(self):
        response = self.client.get("/api/profiles?gender=male")
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data["total"], 2)
        self.assertTrue(all(item["gender"] == "male" for item in data["data"]))

    def test_get_profiles_sort_descending_age(self):
        response = self.client.get("/api/profiles?sort_by=age&order=desc")
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        ages = [item["age"] for item in data["data"]]
        self.assertEqual(ages, sorted(ages, reverse=True))

    def test_get_profiles_invalid_sort_by(self):
        response = self.client.get("/api/profiles?sort_by=height")
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertEqual(data["status"], "error")
        self.assertIn("sort_by must be one of", data["message"])

    def test_get_profiles_pagination_limit_caps(self):
        response = self.client.get("/api/profiles?limit=100")
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data["limit"], 50)

    def test_search_profiles_with_young_males_from_nigeria(self):
        response = self.client.get("/api/profiles/search?q=young+males+from+nigeria")
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data["status"], "success")
        self.assertTrue(all(item["country_id"] == "NG" for item in data["data"]))

    def test_search_profiles_incomprehensible_query(self):
        response = self.client.get("/api/profiles/search?q=xyz123")
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertEqual(data["status"], "error")
        self.assertEqual(data["message"], "Unable to interpret query. Try keywords like: 'male', 'female', 'teenager', 'adult', 'young', 'nigeria', 'kenya', or 'above 30'")

    def test_search_profiles_handles_both_genders(self):
        response = self.client.get("/api/profiles/search?q=male+and+female+teenagers+above+17")
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data["status"], "success")
        self.assertTrue(all(item["age_group"] == "teenager" for item in data["data"]))
        self.assertTrue(all(item["age"] >= 17 for item in data["data"]))
