from django.test import TestCase
from django.urls import reverse


class HomeViewTests(TestCase):
    def test_home_page_loads(self):
        response = self.client.get(reverse("core_v1:home"))
        self.assertEqual(response.status_code, 200)
