from django.urls import reverse

from netbox_sidekick.models import (
    NetworkServiceType, NetworkService
)

from .utils import BaseTest


class MemberTests(BaseTest):
    def test_networkservicetype_basic(self):
        v = NetworkServiceType.objects.get(name="Peering")
        self.assertEqual(v.slug, "peering")

    def test_networkservice_basic(self):
        v = NetworkService.objects.get(member__tenant__name='East University')
        self.assertEqual(v.name, "East University's peering service")

    def test_view_networkservicetype_index(self):
        resp = self.client.get(
            reverse('plugins:netbox_sidekick:networkservicetype_index'))
        self.assertContains(resp, 'Peering')

    def test_view_networkservicetype_detail(self):
        v = NetworkServiceType.objects.get(id=1)
        resp = self.client.get(v.get_absolute_url())
        self.assertContains(resp, 'Peering')
        self.assertContains(resp, "East University&#x27;s peering service")

    def test_view_networkservice_index(self):
        resp = self.client.get(
            reverse('plugins:netbox_sidekick:networkservice_index'))
        self.assertContains(resp, "East University&#x27;s peering service")
