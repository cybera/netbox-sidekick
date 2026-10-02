import netaddr

from django.urls import reverse

from sidekick.models import (
    LogicalSystem, RoutingType,
    NetworkServiceType, NetworkService, NetworkServiceDevice,
    NetworkServiceL2, NetworkServiceL3,
    NetworkServiceGroup,
)

from .test_accounting import _FormsetInputParser
from .utils import BaseTest


class NetworkServiceTest(BaseTest):
    # Logical System
    def test_logicalsystem_basic(self):
        v = LogicalSystem.objects.get(name="Peering")
        self.assertEqual(v.slug, "peering")

    def test_view_logicalsystem_list(self):
        resp = self.client.get(
            reverse('plugins:sidekick:logicalsystem_list'))
        self.assertContains(resp, 'Peering')

    def test_view_logicalsystem_detail(self):
        v = LogicalSystem.objects.get(id=1)
        resp = self.client.get(v.get_absolute_url())
        self.assertContains(resp, 'Peering')

        # Related network services are rendered by an HTMX ObjectsTablePanel, so
        # their rows are not part of the initial page response. Verify the panel
        # is wired to the correctly filtered list endpoint instead.
        self.assertContains(resp, 'logical_system_id=1')
        resp = self.client.get(
            reverse('plugins:sidekick:networkservice_list'),
            {'embedded': 'True', 'logical_system_id': 1},
        )
        self.assertContains(resp, "East University&#x27;s peering service")

    # Network Service Type
    def test_networkservicectype_basic(self):
        v = NetworkServiceType.objects.get(name="Peering")
        self.assertEqual(v.slug, "peering")

    def test_view_networkservicetype_list(self):
        resp = self.client.get(
            reverse('plugins:sidekick:networkservicetype_list'))
        self.assertContains(resp, 'Peering')

    def test_view_networkservicetype_detail(self):
        v = NetworkServiceType.objects.get(id=1)
        resp = self.client.get(v.get_absolute_url())
        self.assertContains(resp, 'Peering')

        # See test_view_logicalsystem_detail for the HTMX panel rationale.
        self.assertContains(resp, 'network_service_type_id=1')
        resp = self.client.get(
            reverse('plugins:sidekick:networkservice_list'),
            {'embedded': 'True', 'network_service_type_id': 1},
        )
        self.assertContains(resp, "East University&#x27;s peering service")

    # Network Service
    def test_networkservice_basic(self):
        v = NetworkService.objects.get(
            member__name='East University',
            description="Peering service for East University")
        self.assertEqual(v.name, "East University's peering service")

    def test_view_networkservice_list(self):
        resp = self.client.get(
            reverse('plugins:sidekick:networkservice_list'))
        self.assertContains(resp, "East University&#x27;s peering service")

    def test_view_networkservice_detail(self):
        # The detail page combines the network service with every device and
        # its L2/L3 components (restored from the pre-4.x sidekick page).
        v = NetworkService.objects.get(id=1)
        resp = self.client.get(v.get_absolute_url())
        self.assertContains(resp, "East University&#x27;s peering service")
        # Device section
        self.assertContains(resp, 'Router 1')
        self.assertContains(resp, 'xe-3/3/3.300')
        # L2 section
        self.assertContains(resp, 'L2 Information')
        # L3 section
        self.assertContains(resp, 'L3 Information')
        self.assertContains(resp, 'Peering')
        self.assertContains(resp, 'BGP')
        self.assertContains(resp, '12345')
        self.assertContains(resp, '192.168.1.1/31')
        self.assertContains(resp, '192.168.1.2/31')
        self.assertContains(resp, '192.168.1.0/24')
        self.assertContains(resp, 'dead:beef::/64')

    # Network Service Group
    def test_networkservicegroup_basic(self):
        ns = NetworkService.objects.get(
            member__name='East University',
            description="Peering service for East University")
        v = NetworkServiceGroup.objects.get(network_services__in=[ns])
        self.assertEqual(v.name, 'A Group')
        self.assertEqual(v.description, 'Just some group')

    def test_view_networkservicegroup_list(self):
        resp = self.client.get(
            reverse('plugins:sidekick:networkservicegroup_list'))
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

    def test_view_routingtype_list(self):
        resp = self.client.get(
            reverse('plugins:sidekick:routingtype_list'))
        self.assertContains(resp, 'BGP')

    def test_view_routingtype_detail(self):
        v = RoutingType.objects.get(id=1)
        resp = self.client.get(v.get_absolute_url())
        self.assertContains(resp, 'BGP')

        # See test_view_logicalsystem_detail for the HTMX panel rationale.
        self.assertContains(resp, 'routing_type_id=1')
        resp = self.client.get(
            reverse('plugins:sidekick:networkservice_list'),
            {'embedded': 'True', 'routing_type_id': 1},
        )
        self.assertContains(resp, "East University&#x27;s peering service")

    # IP Prefixes
    def test_ip_prefixes(self):
        expected_prefixes = [
            netaddr.IPNetwork('192.168.1.0/24'),
            netaddr.IPNetwork('192.168.2.0/24'),
        ]
        v = NetworkService.objects.get(
            member__name='East University',
            description="Peering service for East University")

        prefixes = v.get_prefixes(version=4)
        self.assertEqual(prefixes, expected_prefixes)

    # Backup service
    def test_backup_service(self):
        expected_service_name = "East University's backup peering service"
        v = NetworkService.objects.get(
            member__name='East University',
            description="Peering service for East University")
        backup = v.get_backup_service()[0]
        self.assertEqual(backup.name, expected_service_name)

    # Peering connection
    def test_peeringconnection_get(self):
        v = NetworkServiceL3.objects.get(id=4)
        resp = self.client.get(v.get_peeringconnection_url())
        self.assertContains(resp, 'Peering Partner')
        self.assertContains(resp, 'Internet Exchange')


class NetworkServiceDeviceInlineTest(BaseTest):
    """
    The L2 and L3 services inlines on the NetworkServiceDevice edit page.

    This replaces the Django admin's NetworkServiceL2/L3AdminInline, removed
    with the admin in NetBox 4 (ADR-064). Same form-owned-formset pattern as
    AccountingProfileForm (ADR-073).
    """

    def setUp(self):
        super().setUp()
        self.device = NetworkServiceDevice.objects.get(pk=1)
        self.url = reverse(
            'plugins:sidekick:networkservicedevice_edit', args=[self.device.pk])

    def post_data(self, l3_rows, l2_rows, **overrides):
        """
        Build a POST body for the edit view: the main device fields plus both
        formsets' management data and rows.
        """
        data = {
            'network_service': str(self.device.network_service_id),
            'device': str(self.device.device_id),
            'interface': self.device.interface or '',
            'vlan': str(self.device.vlan) if self.device.vlan is not None else '',
            'comments': self.device.comments or '',
            'legacy_id': self.device.legacy_id or '',
        }
        data.update(overrides)

        for prefix, rows in (('network_service_l3', l3_rows),
                             ('network_service_l2', l2_rows)):
            data[f'{prefix}-TOTAL_FORMS'] = str(len(rows))
            data[f'{prefix}-INITIAL_FORMS'] = str(
                len([r for r in rows if r.get('id')]))
            data[f'{prefix}-MIN_NUM_FORMS'] = '0'
            data[f'{prefix}-MAX_NUM_FORMS'] = '1000'
            for i, row in enumerate(rows):
                for key, value in row.items():
                    data[f'{prefix}-{i}-{key}'] = value
        return data

    def test_edit_page_renders_inlines(self):
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        # Formset management data and existing rows are present.
        self.assertContains(resp, 'network_service_l3-TOTAL_FORMS')
        self.assertContains(resp, 'network_service_l3-0-asn')
        self.assertContains(resp, 'network_service_l2-TOTAL_FORMS')
        self.assertContains(resp, 'network_service_l2-0-vlan')
        # Existing rows are carried as hidden pks, so edits target them.
        self.assertContains(resp, 'network_service_l3-0-id')
        self.assertContains(resp, 'network_service_l2-0-id')
        self.assertContains(resp, 'L3 Services')
        self.assertContains(resp, 'L2 Services')

    def test_inline_adds_l3_and_l2_rows(self):
        l3_rows = [
            {'id': '1', 'logical_system': '1', 'routing_type': '1',
             'asn': '12345', 'ipv4_unicast': 'on', 'ipv4_multicast': '',
             'provider_router_address_ipv4': '192.168.1.1/31',
             'member_router_address_ipv4': '192.168.1.2/31',
             'ipv6_unicast': 'on', 'ipv6_multicast': '',
             'provider_router_address_ipv6': '', 'member_router_address_ipv6': '',
             'comments': ''},
            {'logical_system': '2', 'routing_type': '1', 'asn': '65000',
             'ipv4_unicast': 'on', 'ipv4_multicast': '',
             'provider_router_address_ipv4': '', 'member_router_address_ipv4': '',
             'ipv6_unicast': '', 'ipv6_multicast': '',
             'provider_router_address_ipv6': '', 'member_router_address_ipv6': '',
             'comments': 'transit secondary'},
        ]
        l2_rows = [
            {'id': '1', 'vlan': '300', 'comments': ''},
            {'vlan': '301', 'comments': 'added vlan'},
        ]
        resp = self.client.post(self.url, self.post_data(l3_rows, l2_rows))
        self.assertEqual(resp.status_code, 302)

        new_l3 = NetworkServiceL3.objects.get(asn='65000')
        self.assertEqual(new_l3.network_service_device_id, self.device.pk)
        self.assertEqual(new_l3.logical_system_id, 2)
        new_l2 = NetworkServiceL2.objects.get(vlan=301)
        self.assertEqual(new_l2.network_service_device_id, self.device.pk)
        self.assertEqual(new_l2.comments, 'added vlan')

    def test_inline_edits_l3_row(self):
        l3_rows = [
            {'id': '1', 'logical_system': '1', 'routing_type': '1',
             'asn': '99999', 'ipv4_unicast': 'on', 'ipv4_multicast': 'on',
             'provider_router_address_ipv4': '192.168.1.1/31',
             'member_router_address_ipv4': '192.168.1.2/31',
             'ipv6_unicast': 'on', 'ipv6_multicast': '',
             'provider_router_address_ipv6': '', 'member_router_address_ipv6': '',
             'comments': 'corrected'},
        ]
        l2_rows = [{'id': '1', 'vlan': '300', 'comments': ''}]
        resp = self.client.post(self.url, self.post_data(l3_rows, l2_rows))
        self.assertEqual(resp.status_code, 302)

        updated = NetworkServiceL3.objects.get(pk=1)
        self.assertEqual(updated.asn, '99999')
        self.assertEqual(updated.comments, 'corrected')
        self.assertTrue(updated.ipv4_multicast)
        # An edit must not create a duplicate row.
        self.assertEqual(
            NetworkServiceL3.objects.filter(
                network_service_device=self.device).count(), 1)

    def test_inline_deletes_l2_row(self):
        l3_rows = [
            {'id': '1', 'logical_system': '1', 'routing_type': '1',
             'asn': '12345', 'ipv4_unicast': 'on', 'ipv4_multicast': '',
             'provider_router_address_ipv4': '192.168.1.1/31',
             'member_router_address_ipv4': '192.168.1.2/31',
             'ipv6_unicast': 'on', 'ipv6_multicast': '',
             'provider_router_address_ipv6': '', 'member_router_address_ipv6': '',
             'comments': ''},
        ]
        l2_rows = [{'id': '1', 'vlan': '300', 'comments': '', 'DELETE': 'on'}]
        resp = self.client.post(self.url, self.post_data(l3_rows, l2_rows))
        self.assertEqual(resp.status_code, 302)
        self.assertFalse(
            NetworkServiceL2.objects.filter(network_service_device=self.device).exists())

    def test_submitting_the_rendered_page_unchanged_creates_nothing(self):
        """
        Regression guard for the phantom-row bug shape (see
        AccountingProfileInlineTest and ADR-073): submit the edit page exactly
        as it renders -- including the initial-* hidden inputs Django renders
        for change detection -- and nothing must be created.
        """
        html = self.client.get(self.url).content.decode()
        parsed = {}
        for prefix in ('network_service_l3', 'network_service_l2'):
            parser = _FormsetInputParser(f'{prefix}-')
            parser.feed(html)
            parsed[prefix] = parser.values
            # Sanity: the page really did render this formset, blank row
            # included (existing row ids plus one extra form).
            self.assertIn(f'{prefix}-TOTAL_FORMS', parser.values)
            self.assertIn(f'{prefix}-INITIAL_FORMS', parser.values)

        data = self.post_data([], [])
        for prefix, values in parsed.items():
            for key, value in values.items():
                data[key] = value

        resp = self.client.post(self.url, data)
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(
            NetworkServiceL3.objects.filter(
                network_service_device=self.device).count(), 1,
            'saving the device untouched must not create an L3 service',
        )
        self.assertEqual(
            NetworkServiceL2.objects.filter(
                network_service_device=self.device).count(), 1,
            'saving the device untouched must not create an L2 service',
        )

    def test_invalid_l3_row_blocks_the_whole_save(self):
        l3_rows = [
            {'id': '1', 'logical_system': '1', 'routing_type': '1',
             'asn': '12345', 'ipv4_unicast': 'on', 'ipv4_multicast': '',
             'provider_router_address_ipv4': '192.168.1.1/31',
             'member_router_address_ipv4': '192.168.1.2/31',
             'ipv6_unicast': 'on', 'ipv6_multicast': '',
             'provider_router_address_ipv6': '', 'member_router_address_ipv6': '',
             'comments': ''},
            # Nonexistent FK: the formset must reject it.
            {'logical_system': '999999', 'routing_type': '1', 'asn': '65000',
             'ipv4_unicast': 'on', 'ipv4_multicast': '',
             'provider_router_address_ipv4': '', 'member_router_address_ipv4': '',
             'ipv6_unicast': '', 'ipv6_multicast': '',
             'provider_router_address_ipv6': '', 'member_router_address_ipv6': '',
             'comments': ''},
        ]
        l2_rows = [{'id': '1', 'vlan': '300', 'comments': ''}]
        resp = self.client.post(self.url, self.post_data(l3_rows, l2_rows))
        # Re-rendered, not redirected.
        self.assertEqual(resp.status_code, 200)
        # Nothing was written anywhere: the bad row is rejected and the valid
        # L2 row is not saved either, because the whole form is invalid.
        self.assertFalse(
            NetworkServiceL3.objects.filter(asn='65000').exists())
        self.assertEqual(
            NetworkServiceL2.objects.filter(
                network_service_device=self.device).count(), 1)

    def test_invalid_l2_row_blocks_the_whole_save(self):
        l3_rows = [
            {'id': '1', 'logical_system': '1', 'routing_type': '1',
             'asn': '12345', 'ipv4_unicast': 'on', 'ipv4_multicast': '',
             'provider_router_address_ipv4': '192.168.1.1/31',
             'member_router_address_ipv4': '192.168.1.2/31',
             'ipv6_unicast': 'on', 'ipv6_multicast': '',
             'provider_router_address_ipv6': '', 'member_router_address_ipv6': '',
             'comments': ''},
        ]
        l2_rows = [
            {'id': '1', 'vlan': '300', 'comments': ''},
            # Not an integer: the formset must reject it.
            {'vlan': 'not-a-number', 'comments': ''},
        ]
        resp = self.client.post(self.url, self.post_data(l3_rows, l2_rows))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(
            NetworkServiceL3.objects.filter(
                network_service_device=self.device).count(), 1)
        self.assertEqual(
            NetworkServiceL2.objects.filter(
                network_service_device=self.device).count(), 1)

    def test_inline_on_add_page_creates_device_with_rows(self):
        url = reverse('plugins:sidekick:networkservicedevice_add')
        data = {
            'network_service': '1',
            'device': '1',
            'interface': 'xe-3/3/4.300',
            'vlan': '300',
            'comments': '',
            'legacy_id': '',
            'network_service_l3-TOTAL_FORMS': '1',
            'network_service_l3-INITIAL_FORMS': '0',
            'network_service_l3-MIN_NUM_FORMS': '0',
            'network_service_l3-MAX_NUM_FORMS': '1000',
            'network_service_l3-0-logical_system': '2',
            'network_service_l3-0-routing_type': '1',
            'network_service_l3-0-asn': '65001',
            'network_service_l3-0-ipv4_unicast': 'on',
            'network_service_l3-0-ipv4_multicast': '',
            'network_service_l3-0-provider_router_address_ipv4': '',
            'network_service_l3-0-member_router_address_ipv4': '',
            'network_service_l3-0-ipv6_unicast': '',
            'network_service_l3-0-ipv6_multicast': '',
            'network_service_l3-0-provider_router_address_ipv6': '',
            'network_service_l3-0-member_router_address_ipv6': '',
            'network_service_l3-0-comments': '',
            'network_service_l2-TOTAL_FORMS': '1',
            'network_service_l2-INITIAL_FORMS': '0',
            'network_service_l2-MIN_NUM_FORMS': '0',
            'network_service_l2-MAX_NUM_FORMS': '1000',
            'network_service_l2-0-vlan': '301',
            'network_service_l2-0-comments': '',
        }
        resp = self.client.post(url, data)
        self.assertEqual(resp.status_code, 302)

        new = NetworkServiceDevice.objects.get(interface='xe-3/3/4.300')
        self.assertEqual(new.network_service_id, 1)
        l3 = NetworkServiceL3.objects.get(network_service_device=new)
        self.assertEqual(l3.asn, '65001')
        self.assertTrue(l3.active)  # inline rows default to active
        l2 = NetworkServiceL2.objects.get(network_service_device=new)
        self.assertEqual(l2.vlan, 301)
