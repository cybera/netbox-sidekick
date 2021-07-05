import netaddr

from django.urls import reverse

from sidekick.models import (
    LogicalSystem, RoutingType,
    NetworkServiceType, NetworkService,
    NetworkServiceGroup,
)

from .utils import BaseTest


class NetworkServiceTest(BaseTest):
    # Logical System
    def test_logicalsystem_basic(self):
        v = LogicalSystem.objects.get(name="Peering")
        self.assertEqual(v.slug, "peering")

    def test_view_logicalsystem_index(self):
        resp = self.client.get(
            reverse('plugins:sidekick:logicalsystem_index'))
        self.assertContains(resp, 'Peering')

    def test_view_logicalsystem_detail(self):
        v = LogicalSystem.objects.get(id=1)
        resp = self.client.get(v.get_absolute_url())
        self.assertContains(resp, 'Peering')
        self.assertContains(resp, "East University&#x27;s peering service")

    # Network Service Type
    def test_networkservicectype_basic(self):
        v = NetworkServiceType.objects.get(name="Peering")
        self.assertEqual(v.slug, "peering")

    def test_view_networkservicetype_index(self):
        resp = self.client.get(
            reverse('plugins:sidekick:networkservicetype_index'))
        self.assertContains(resp, 'Peering')

    def test_view_networkservicetype_detail(self):
        v = NetworkServiceType.objects.get(id=1)
        resp = self.client.get(v.get_absolute_url())
        self.assertContains(resp, 'Peering')
        self.assertContains(resp, "East University&#x27;s peering service")

    # Network Service
    def test_networkservice_basic(self):
        v = NetworkService.objects.get(member__name='East University')
        self.assertEqual(v.name, "East University's peering service")

    def test_view_networkservice_index(self):
        resp = self.client.get(
            reverse('plugins:sidekick:networkservice_index'))
        self.assertContains(resp, "East University&#x27;s peering service")

    # Network Service Group
    def test_networkservicegroup_basic(self):
        ns = NetworkService.objects.get(member__name='East University')
        v = NetworkServiceGroup.objects.get(network_services__in=[ns])
        self.assertEqual(v.name, 'A Group')
        self.assertEqual(v.description, 'Just some group')

    def test_view_networkservicegroup_index(self):
        resp = self.client.get(
            reverse('plugins:sidekick:networkservicegroup_index'))
        self.assertContains(resp, 'A Group')
        self.assertContains(resp, 'Just some group')

    def test_view_networkservicegroup_detail(self):
        v = NetworkServiceGroup.objects.get(id=1)
        resp = self.client.get(v.get_absolute_url())
        self.assertContains(resp, 'A Group')
        self.assertContains(resp, 'Just some group')

    # Routing Type
    def test_routingtype_basic(self):
        v = RoutingType.objects.get(name="BGP")
        self.assertEqual(v.slug, "bgp")

    def test_view_routingtype_index(self):
        resp = self.client.get(
            reverse('plugins:sidekick:routingtype_index'))
        self.assertContains(resp, 'BGP')

    def test_view_routingtype_detail(self):
        v = RoutingType.objects.get(id=1)
        resp = self.client.get(v.get_absolute_url())
        self.assertContains(resp, 'BGP')
        self.assertContains(resp, "East University&#x27;s peering service")

    # IP Prefixes
    def test_ip_prefixes(self):
        expected_prefixes = [
            netaddr.IPNetwork('192.168.1.0/24'),
            netaddr.IPNetwork('192.168.2.0/24'),
        ]
        v = NetworkService.objects.get(member__name='East University')
        prefixes = v.get_ipv4_prefixes()
        self.assertEqual(prefixes, expected_prefixes)
