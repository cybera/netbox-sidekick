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


class AdminParityTest(BaseTest):
    """
        Parity between the removed Django admin's edit pages (deleted with
        NetBox 4.2, ADR-064) and the plugin's forms.

        Every check here documents a behaviour the old admin had and the
        first-class plugin forms initially lacked.

        The slug fields: the admin exposed slug (and NetworkServiceType's
        description) on its default edit pages. The rewritten forms omitted
        them, so a UI-created LogicalSystem got an empty slug and a second
        create failed with an IntegrityError. The forms now use NetBox's
        SlugField (auto-populate from name), like core NetBox forms.
    """

    def test_logicalsystem_create_with_slug(self):
        url = reverse('plugins:sidekick:logicalsystem_add')
        resp = self.client.post(
            url, {'name': 'West College', 'slug': 'west-college'})
        try:
            form_errors = dict(resp.context['form'].errors)
        except (AttributeError, KeyError, TypeError):
            form_errors = {}
        self.assertEqual(resp.status_code, 302, msg=f'form errors: {form_errors}')
        self.assertTrue(LogicalSystem.objects.filter(
            name='West College', slug='west-college').exists())

    def test_logicalsystem_create_without_slug_is_rejected(self):
        # Regression: this used to save with an empty slug, and a second
        # create blew up with an IntegrityError (slug is unique, NOT NULL).
        url = reverse('plugins:sidekick:logicalsystem_add')
        count = LogicalSystem.objects.count()
        resp = self.client.post(url, {'name': 'Transit'})
        self.assertEqual(resp.status_code, 200)  # re-render with errors
        self.assertContains(resp, 'This field is required', status_code=200)
        self.assertEqual(LogicalSystem.objects.count(), count)

    def test_networkservicetype_create_with_description(self):
        # The admin's NetworkServiceType page exposed the description field.
        url = reverse('plugins:sidekick:networkservicetype_add')
        resp = self.client.post(url, {
            'name': 'Transit', 'slug': 'transit',
            'description': 'Transit services',
        })
        self.assertEqual(resp.status_code, 302)
        v = NetworkServiceType.objects.get(name='Transit')
        self.assertEqual(v.description, 'Transit services')

    def test_device_form_service_dropdown_excludes_inactive_services(self):
        # The admin's NetworkServiceDevice page only offered active services
        # (plus, here, the edited device's own service), ordered by member.
        from sidekick.forms import NetworkServiceDeviceForm
        inactive = NetworkService.objects.get(pk=4)
        self.assertFalse(inactive.active)

        # Add form: the inactive service is not offered.
        form = NetworkServiceDeviceForm()
        offered = set(form.fields['network_service'].queryset.values_list(
            'pk', flat=True))
        self.assertNotIn(inactive.pk, offered)
        self.assertIn(NetworkService.objects.get(pk=1).pk, offered)

        # Edit form of a device attached to the inactive service: the
        # instance's current service stays selectable, or the edit could
        # never be saved.
        device = NetworkServiceDevice.objects.get(pk=4)
        form = NetworkServiceDeviceForm(instance=device)
        self.assertIn(
            inactive.pk,
            set(form.fields['network_service'].queryset.values_list(
                'pk', flat=True)))

    def test_device_list_active_filter_defaults_to_active(self):
        # The admin's device list showed active services by default.
        url = reverse('plugins:sidekick:networkservicedevice_list')
        resp = self.client.get(url)
        self.assertContains(resp, 'xe-3/3/3.300')
        self.assertNotContains(resp, 'xe-3/3/3.400')

        # An explicit No shows only the inactive ones.
        resp = self.client.get(url, {'active': 'false'})
        self.assertContains(resp, 'xe-3/3/3.400')
        self.assertNotContains(resp, 'xe-3/3/3.300')


class NetworkServiceInlineTest(BaseTest):
    """
    The NetworkServiceDevice inline on the NetworkService edit page: CRUD of
    devices and their L2/L3 components from the service itself.

    A device row is a formset row; each existing device row carries its own
    L2/L3 formsets (nested prefixes), and a new device row carries a single
    L2 row and a single L3 row created in the same save.
    """

    def setUp(self):
        super().setUp()
        self.service = NetworkService.objects.get(pk=1)
        self.device = NetworkServiceDevice.objects.get(pk=1)
        self.url = reverse('plugins:sidekick:networkservice_edit',
                           args=[self.service.pk])

    def service_fields(self, **overrides):
        data = {
            'name': self.service.name,
            'network_service_type': str(self.service.network_service_type_id),
            'member': str(self.service.member_id),
            'member_site': str(self.service.member_site_id),
            'start_date': '2026-10-01 00:00:00',
            'end_date': '',
            'description': self.service.description or '',
            'comments': self.service.comments or '',
            'active': 'on',
            'legacy_id': str(self.service.legacy_id) if self.service.legacy_id else '',
            'backup_for': str(self.service.backup_for_id) if self.service.backup_for_id else '',
            'accounting_profile': str(self.service.accounting_profile_id) if self.service.accounting_profile_id else '',
        }
        data.update(overrides)
        return data

    def device_row(self, index, existing_id, **overrides):
        data = {
            f'network_service_device-{index}-id': str(existing_id or ''),
            f'network_service_device-{index}-device': str(self.device.device_id),
            f'network_service_device-{index}-interface': self.device.interface or '',
            f'network_service_device-{index}-vlan': str(self.device.vlan or ''),
            f'network_service_device-{index}-comments': self.device.comments or '',
        }
        data.update({f'network_service_device-{index}-{k}': v
                     for k, v in overrides.items()})
        return data

    def device_mgmt(self, total, initial):
        return {
            'network_service_device-TOTAL_FORMS': str(total),
            'network_service_device-INITIAL_FORMS': str(initial),
            'network_service_device-MIN_NUM_FORMS': '0',
            'network_service_device-MAX_NUM_FORMS': '1000',
        }

    def l3_rows(self, index, rows):
        data = {
            f'network_service_device-{index}-network_service_l3-TOTAL_FORMS': str(len(rows)),
            f'network_service_device-{index}-network_service_l3-INITIAL_FORMS': str(
                len([r for r in rows if r.get('id')])),
            f'network_service_device-{index}-network_service_l3-MIN_NUM_FORMS': '0',
            f'network_service_device-{index}-network_service_l3-MAX_NUM_FORMS': '1000',
        }
        for i, row in enumerate(rows):
            for key, value in row.items():
                data[f'network_service_device-{index}-network_service_l3-{i}-{key}'] = value
        return data

    def l2_rows(self, index, rows):
        data = {
            f'network_service_device-{index}-network_service_l2-TOTAL_FORMS': str(len(rows)),
            f'network_service_device-{index}-network_service_l2-INITIAL_FORMS': str(
                len([r for r in rows if r.get('id')])),
            f'network_service_device-{index}-network_service_l2-MIN_NUM_FORMS': '0',
            f'network_service_device-{index}-network_service_l2-MAX_NUM_FORMS': '1000',
        }
        for i, row in enumerate(rows):
            for key, value in row.items():
                data[f'network_service_device-{index}-network_service_l2-{i}-{key}'] = value
        return data

    def test_edit_page_renders_device_inline(self):
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Network Service Devices')
        # Device formset management data and the existing row.
        self.assertContains(resp, 'network_service_device-TOTAL_FORMS')
        self.assertContains(resp, 'network_service_device-0-id')
        self.assertContains(resp, 'xe-3/3/3.300')
        # The existing device row carries its L2/L3 formsets.
        self.assertContains(resp,
                            'network_service_device-0-network_service_l3-TOTAL_FORMS')
        self.assertContains(resp, 'network_service_device-0-network_service_l3-0-asn')
        self.assertContains(resp, 'network_service_device-0-network_service_l2-0-vlan')
        # The extra (new) device row carries single L2/L3 forms.
        self.assertContains(resp, 'network_service_device-1-network_service_l2-vlan')
        self.assertContains(resp, 'network_service_device-1-network_service_l3-asn')
        # Existing device rows can be deleted.
        self.assertContains(resp, 'network_service_device-0-DELETE')

    def test_edit_updates_existing_device_l2_l3(self):
        data = self.service_fields()
        data.update(self.device_row(0, self.device.pk))
        data.update(self.l3_rows(0, [
            {'id': '1', 'logical_system': '1', 'routing_type': '1',
             'asn': '12399', 'ipv4_unicast': 'on', 'ipv4_multicast': '',
             'provider_router_address_ipv4': '192.168.1.1/31',
             'member_router_address_ipv4': '192.168.1.2/31',
             'ipv6_unicast': 'on', 'ipv6_multicast': '',
             'provider_router_address_ipv6': '', 'member_router_address_ipv6': '',
             'comments': ''},
        ]))
        data.update(self.l2_rows(0, [
            {'id': '1', 'vlan': '333', 'comments': 'updated'},
        ]))
        # An untouched extra device row.
        data.update(self.device_row(1, None))
        data.update(self.device_mgmt(2, 1))
        resp = self.client.post(self.url, data)
        try:
            dbg = (dict(resp.context['form'].errors),
                   [dict(f.errors) for f in resp.context['form'].device_formset],
                   resp.context['form'].device_formset.non_form_errors())
        except Exception as e:  # pragma: no cover
            dbg = f'debug failed: {e}'
        self.assertEqual(resp.status_code, 302, msg=dbg)
        self.device.refresh_from_db()
        l3 = NetworkServiceL3.objects.get(pk=1)
        self.assertEqual(l3.asn, '12399')
        l2 = NetworkServiceL2.objects.get(pk=1)
        self.assertEqual(l2.vlan, 333)
        self.assertEqual(l2.comments, 'updated')

    def test_edit_adds_device_with_l2_and_l3(self):
        data = self.service_fields()
        data.update(self.device_row(0, self.device.pk))
        data.update(self.l3_rows(0, [
            {'id': '1', 'logical_system': '1', 'routing_type': '1',
             'asn': '12345', 'ipv4_unicast': 'on', 'ipv4_multicast': '',
             'provider_router_address_ipv4': '192.168.1.1/31',
             'member_router_address_ipv4': '192.168.1.2/31',
             'ipv6_unicast': 'on', 'ipv6_multicast': '',
             'provider_router_address_ipv6': '', 'member_router_address_ipv6': '',
             'comments': ''},
        ]))
        data.update(self.l2_rows(0, [
            {'id': '1', 'vlan': '300', 'comments': ''},
        ]))
        # The new device row, with its single L2 and L3 rows.
        data.update(self.device_row(1, None, interface='xe-3/3/3.400', vlan='400'))
        data['network_service_device-1-network_service_l2-vlan'] = '400'
        data['network_service_device-1-network_service_l2-comments'] = ''
        data['network_service_device-1-network_service_l3-logical_system'] = '2'
        data['network_service_device-1-network_service_l3-routing_type'] = '1'
        data['network_service_device-1-network_service_l3-asn'] = '65001'
        data['network_service_device-1-network_service_l3-ipv4_unicast'] = 'on'
        data['network_service_device-1-network_service_l3-ipv4_multicast'] = ''
        data['network_service_device-1-network_service_l3-provider_router_address_ipv4'] = ''
        data['network_service_device-1-network_service_l3-member_router_address_ipv4'] = ''
        data['network_service_device-1-network_service_l3-ipv6_unicast'] = ''
        data['network_service_device-1-network_service_l3-ipv6_multicast'] = ''
        data['network_service_device-1-network_service_l3-provider_router_address_ipv6'] = ''
        data['network_service_device-1-network_service_l3-member_router_address_ipv6'] = ''
        data['network_service_device-1-network_service_l3-comments'] = ''
        data.update(self.device_mgmt(2, 1))

        resp = self.client.post(self.url, data)
        try:
            dbg = (dict(resp.context['form'].errors),
                   [dict(f.errors) for f in resp.context['form'].device_formset],
                   resp.context['form'].device_formset.non_form_errors())
        except Exception as e:  # pragma: no cover
            dbg = f'debug failed: {e}'
        self.assertEqual(resp.status_code, 302, msg=dbg)

        new_device = NetworkServiceDevice.objects.get(
            network_service=self.service, interface='xe-3/3/3.400')
        self.assertEqual(new_device.vlan, 400)
        l3 = NetworkServiceL3.objects.get(network_service_device=new_device)
        self.assertEqual(l3.asn, '65001')
        self.assertEqual(l3.logical_system_id, 2)
        self.assertTrue(l3.active)
        l2 = NetworkServiceL2.objects.get(network_service_device=new_device)
        self.assertEqual(l2.vlan, 400)

    def test_edit_cannot_delete_device_with_components(self):
        data = self.service_fields()
        data.update(self.device_row(0, self.device.pk, DELETE='on'))
        data.update(self.l3_rows(0, [
            {'id': '1', 'logical_system': '1', 'routing_type': '1',
             'asn': '12345', 'ipv4_unicast': 'on', 'ipv4_multicast': '',
             'provider_router_address_ipv4': '192.168.1.1/31',
             'member_router_address_ipv4': '192.168.1.2/31',
             'ipv6_unicast': 'on', 'ipv6_multicast': '',
             'provider_router_address_ipv6': '', 'member_router_address_ipv6': '',
             'comments': ''},
        ]))
        data.update(self.l2_rows(0, [
            {'id': '1', 'vlan': '300', 'comments': ''},
        ]))
        data.update(self.device_row(1, None))
        data.update(self.device_mgmt(2, 1))
        resp = self.client.post(self.url, data)
        self.assertEqual(resp.status_code, 200)  # re-render with the blocker
        self.assertTrue(NetworkServiceDevice.objects.filter(pk=self.device.pk).exists())
        self.assertTrue(NetworkServiceL3.objects.filter(pk=1).exists())

    def test_edit_deletes_device_without_components(self):
        extra = NetworkServiceDevice.objects.create(
            network_service=self.service, device_id=1,
            interface='xe-3/3/3.500', vlan=500)

        data = self.service_fields()
        data.update(self.device_row(0, self.device.pk))
        data.update(self.l3_rows(0, [
            {'id': '1', 'logical_system': '1', 'routing_type': '1',
             'asn': '12345', 'ipv4_unicast': 'on', 'ipv4_multicast': '',
             'provider_router_address_ipv4': '192.168.1.1/31',
             'member_router_address_ipv4': '192.168.1.2/31',
             'ipv6_unicast': 'on', 'ipv6_multicast': '',
             'provider_router_address_ipv6': '', 'member_router_address_ipv6': '',
             'comments': ''},
        ]))
        data.update(self.l2_rows(0, [
            {'id': '1', 'vlan': '300', 'comments': ''},
        ]))
        # Two device rows now: index 0 existing-with-components, index 1 the
        # bare device to delete, index 2 the untouched extra row.
        data.update(self.device_row(1, extra.pk, DELETE='on',
                                    interface='xe-3/3/3.500', vlan='500'))
        data.update(self.device_row(2, None))
        data.update(self.device_mgmt(3, 2))
        resp = self.client.post(self.url, data)
        try:
            dbg = (dict(resp.context['form'].errors),
                   [dict(f.errors) for f in resp.context['form'].device_formset],
                   resp.context['form'].device_formset.non_form_errors())
        except Exception as e:  # pragma: no cover
            dbg = f'debug failed: {e}'
        self.assertEqual(resp.status_code, 302, msg=dbg)
        self.assertFalse(NetworkServiceDevice.objects.filter(pk=extra.pk).exists())
        self.assertTrue(NetworkServiceDevice.objects.filter(pk=self.device.pk).exists())

    def test_add_page_renders_inline(self):
        url = reverse('plugins:sidekick:networkservice_add')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Network Service Devices')
        self.assertContains(resp, 'network_service_device-TOTAL_FORMS')
        self.assertContains(resp, 'network_service_device-0-network_service_l2-vlan')
        self.assertContains(resp, 'network_service_device-0-network_service_l3-asn')

    def test_edit_updates_prefixes_from_inline(self):
        data = self.service_fields()
        data.update(self.device_row(0, self.device.pk))
        data.update(self.l3_rows(0, [
            {'id': '1', 'logical_system': '1', 'routing_type': '1',
             'asn': '12345', 'ipv4_unicast': 'on', 'ipv4_multicast': '',
             'provider_router_address_ipv4': '192.168.1.1/31',
             'member_router_address_ipv4': '192.168.1.2/31',
             'ipv6_unicast': 'on', 'ipv6_multicast': '',
             'provider_router_address_ipv6': '', 'member_router_address_ipv6': '',
             'ip_prefixes': ['1', '2'],
             'comments': ''},
        ]))
        data.update(self.l2_rows(0, [
            {'id': '1', 'vlan': '300', 'comments': ''},
        ]))
        data.update(self.device_row(1, None))
        data.update(self.device_mgmt(2, 1))
        resp = self.client.post(self.url, data)
        self.assertEqual(resp.status_code, 302)
        l3 = NetworkServiceL3.objects.get(pk=1)
        self.assertEqual(
            set(l3.ip_prefixes.values_list('pk', flat=True)), {1, 2})
