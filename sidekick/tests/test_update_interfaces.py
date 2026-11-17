"""Regression test for the SNMP Counter64 overflow that broke NIC polling.

``update_interfaces`` stores raw SNMP counters into ``NIC`` bigint columns.
Some devices report Counter64 values >= 2**63 -- observed on the Juniper ``irb``
interfaces of the Calgary/Edmonton Core Routers, where ``ifHCInUcastPkts``
comes back as ``18446744073706646512`` (2**64 - 2905104). PostgreSQL rejects
those with ``ERROR: bigint out of range``, and because the command catches the
``DataError`` and skips the row, every counter for that interface was silently
dropped (the production log filled with ~576 such errors per day).

``sanitize_counter`` maps out-of-range (and non-numeric) values to 0 so the NIC
row is stored instead of aborted.
"""

from django.test import TestCase

from dcim.choices import InterfaceModeChoices, InterfaceTypeChoices
from dcim.models import Device, Interface

from sidekick.management.commands.update_interfaces import (
    SIGNED_BIGINT_MAX,
    build_interface,
    interface_enabled,
    interface_type_from_speed,
    resolve_interface_name,
    sanitize_counter,
)
from sidekick.utils import index_interfaces_by_mac
from sidekick.tests.utils import BaseTest


class SanitizeCounterTest(TestCase):
    def test_production_overflow_value_is_rejected(self):
        # Exact value seen in the production Postgres log on 2026-10-10.
        self.assertEqual(sanitize_counter('18446744073706646512'), 0)
        self.assertEqual(sanitize_counter(18446744073706646512), 0)

    def test_signed_bigint_boundaries(self):
        self.assertEqual(sanitize_counter(SIGNED_BIGINT_MAX), SIGNED_BIGINT_MAX)
        self.assertEqual(sanitize_counter(2 ** 63), 0)
        self.assertEqual(sanitize_counter(2 ** 64 - 1), 0)

    def test_normal_values_pass_through(self):
        self.assertEqual(sanitize_counter(0), 0)
        self.assertEqual(sanitize_counter('12345'), 12345)
        self.assertEqual(sanitize_counter(2 ** 62), 2 ** 62)

    def test_negative_and_non_numeric_are_rejected(self):
        self.assertEqual(sanitize_counter(-1), 0)
        self.assertEqual(sanitize_counter('No more variables left in this MIB View'), 0)
        self.assertEqual(sanitize_counter(None), 0)
        self.assertEqual(sanitize_counter(''), 0)


class SanitizeCounterIsQuietTest(TestCase):
    """The sanitiser must not write to WARNING or above.

    Cron mails a job's stderr, and Django logs WARNING to stderr. This condition
    is permanent hardware behaviour, so a warning here turned into two emails
    every five minutes: 4,133 of them between 2026-10-12 and 2026-10-27.
    Anything at WARNING or above in this code path reaches the operator's inbox
    288 times a day.
    """

    def test_no_warning_is_logged_for_an_overflow_value(self):
        with self.assertNoLogs('sidekick.management.commands.update_interfaces', level='WARNING'):
            self.assertEqual(sanitize_counter('18446744073700172065', context='irb.27'), 0)

    def test_the_value_is_still_discarded(self):
        self.assertEqual(sanitize_counter('18446744073700172065'), 0)

    def test_debug_still_records_it(self):
        with self.assertLogs(
            'sidekick.management.commands.update_interfaces', level='DEBUG'
        ) as captured:
            sanitize_counter('18446744073700172065', context='irb.27')
        self.assertIn('out-of-range', '\n'.join(captured.output))
        self.assertIn('irb.27', '\n'.join(captured.output))


class MissingWalkFieldTest(TestCase):
    """A truncated SNMP walk must not abort the poll for a whole device.

    On 2026-11-11 to 2026-11-16 the core-router poller mailed
    ``KeyError: 'ifHighSpeed'`` from ``update_interfaces``. ``results`` in
    ``snmpwalk_bulk`` gets an entry for an interface as soon as *any* walked
    OID returns a row for it, and a walk can stop before every OID has been
    returned for every interface -- the module already notes that case for the
    "No more variables left in this MIB View" replies. Indexing the missing
    field killed the run, so every interface after it on that device went
    unpollled and cron mailed the netbox account every five minutes.
    """

    def test_unknown_speed_falls_back_to_virtual(self):
        self.assertEqual(
            interface_type_from_speed(None), InterfaceTypeChoices.TYPE_VIRTUAL)
        self.assertEqual(
            interface_type_from_speed(''), InterfaceTypeChoices.TYPE_VIRTUAL)

    def test_known_speeds_map_to_their_types(self):
        self.assertEqual(
            interface_type_from_speed('1000'), InterfaceTypeChoices.TYPE_1GE_FIXED)
        self.assertEqual(
            interface_type_from_speed('10000'), InterfaceTypeChoices.TYPE_10GE_FIXED)
        self.assertEqual(
            interface_type_from_speed('100000'), InterfaceTypeChoices.TYPE_100GE_QSFP28)
        self.assertEqual(
            interface_type_from_speed('ieee8023adLag'), InterfaceTypeChoices.TYPE_LAG)

    def test_missing_status_leaves_the_stored_value_alone(self):
        self.assertIsNone(interface_enabled(None, 1))
        self.assertIsNone(interface_enabled('up', None))
        self.assertIsNone(interface_enabled(None, None))

    def test_present_statuses_still_decide(self):
        self.assertTrue(interface_enabled('up', 1))
        self.assertFalse(interface_enabled('down', 1))
        self.assertFalse(interface_enabled('up', 2))


class BuildInterfaceTest(BaseTest):
    """Creating an Interface from a walk entry must work on NetBox 4.

    NetBox 4 removed ``Interface.mac_address``. The poller still passed it to
    the constructor, so every interface that appeared on a device after the 4.7
    cutover failed to be created and the device poll aborted:
    ``TypeError: Interface() got unexpected keyword arguments: 'mac_address'``
    (mails from ``update_devices_all_else.sh`` every five minutes from
    2026-11-17 18:59 UTC).
    """

    def setUp(self):
        super().setUp()
        self.device = Device.objects.get(pk=1)

    def _details(self, **extra):
        details = {
            'ifName': 'ge-0/0/9',
            'ifDescr': 'Test uplink',
            'ifAdminStatus': 'up',
            'ifOperStatus': 1,
            'ifMtu': '1500',
            'ifPhysAddress': 'ec:f4:bb:c1:79:b8',
        }
        details.update(extra)
        return details

    def test_interface_is_created_with_its_mac(self):
        iface = build_interface(
            self.device, 'ge-0/0/9', self._details(),
            InterfaceTypeChoices.TYPE_1GE_FIXED, InterfaceModeChoices.MODE_TAGGED)

        self.assertEqual(iface.name, 'ge-0/0/9')
        self.assertEqual(iface.description, 'Test uplink')
        self.assertTrue(iface.enabled)
        self.assertEqual(iface.mtu, 1500)
        self.assertIsNotNone(iface.primary_mac_address)
        self.assertEqual(f"{iface.primary_mac_address}", 'EC:F4:BB:C1:79:B8')

    def test_missing_mac_leaves_it_unset(self):
        details = self._details(**{'ifPhysAddress': None})
        iface = build_interface(
            self.device, 'ge-0/0/10', details,
            InterfaceTypeChoices.TYPE_1GE_FIXED, InterfaceModeChoices.MODE_TAGGED)

        self.assertIsNone(iface.primary_mac_address)

    def test_admin_down_creates_a_disabled_interface(self):
        details = self._details(**{'ifAdminStatus': 'down'})
        iface = build_interface(
            self.device, 'ge-0/0/11', details,
            InterfaceTypeChoices.TYPE_1GE_FIXED, InterfaceModeChoices.MODE_TAGGED)

        self.assertFalse(iface.enabled)

    def test_unparsed_mtu_does_not_break_creation(self):
        # ifMtu is a string from the walk, and NetBox's full_clean (run by the
        # MAC setter) rejects a string or a below-minimum value. Unknown means
        # NULL; the old code passed 0, which validation rejects as well.
        details = self._details(**{
            'ifMtu': 'No more variables left in this MIB View',
            'ifPhysAddress': 'ec:f4:bb:c1:79:b9',
        })
        iface = build_interface(
            self.device, 'ge-0/0/12', details,
            InterfaceTypeChoices.TYPE_1GE_FIXED, InterfaceModeChoices.MODE_TAGGED)

        self.assertIsNone(iface.mtu)

    def test_mtu_is_stored_as_an_integer(self):
        iface = build_interface(
            self.device, 'ge-0/0/13', self._details(),
            InterfaceTypeChoices.TYPE_1GE_FIXED, InterfaceModeChoices.MODE_TAGGED)

        self.assertEqual(iface.mtu, 1500)


class ResolveInterfaceNameTest(BaseTest):
    """Matching a polled interface to a NetBox interface when the name is not the port's.

    An ASA reports the interface's nameif in both ifName and ifDescr, so
    Ethernet1/2 arrives as "inside" and no name lookup finds it (verified on
    vpn2, 2026-11-17: ifIndex 6, ifName "inside", MAC f8:e5:7e:17:07:a5). The
    port is recorded only when an operator creates the NetBox interface and
    gives it the port's MAC, so the poller has to match on that MAC.
    """

    def setUp(self):
        super().setUp()
        self.device = Device.objects.get(pk=1)
        self.port = Interface.objects.create(
            device=self.device, name='Ethernet1/2',
            type=InterfaceTypeChoices.TYPE_1GE_FIXED)
        self.port.set_primary_mac_address_from_value('f8:e5:7e:17:07:a5')
        self.port.save()

    def _existing(self):
        return {i.name: i for i in self.device.vc_interfaces()}

    def _by_mac(self):
        return index_interfaces_by_mac(self._existing().values())

    def test_name_match_wins(self):
        details = {'ifName': 'Ethernet1/2', 'ifPhysAddress': 'f8:e5:7e:17:07:a5'}
        self.assertEqual(
            resolve_interface_name(details, self._existing(), self._by_mac()),
            'Ethernet1/2')

    def test_nameif_is_resolved_through_the_mac(self):
        details = {'ifName': 'inside', 'ifPhysAddress': 'f8:e5:7e:17:07:a5'}
        self.assertEqual(
            resolve_interface_name(details, self._existing(), self._by_mac()),
            'Ethernet1/2')

    def test_mac_comparison_ignores_case_and_separator(self):
        # SNMP returns lower case; NetBox stores and displays upper case.
        details = {'ifName': 'inside', 'ifPhysAddress': 'F8-E5-7E-17-07-A5'}
        self.assertEqual(
            resolve_interface_name(details, self._existing(), self._by_mac()),
            'Ethernet1/2')

    def test_unrecognised_name_without_a_mac_match_is_skipped(self):
        details = {'ifName': 'nlp_int_tap', 'ifPhysAddress': '00:00:01:00:00:01'}
        self.assertIsNone(
            resolve_interface_name(details, self._existing(), self._by_mac()))

    def test_unrecognised_name_without_a_mac_is_skipped(self):
        self.assertIsNone(
            resolve_interface_name({'ifName': 'outside'}, self._existing(), self._by_mac()))

    def test_valid_name_not_yet_in_netbox_is_created(self):
        details = {'ifName': 'Ethernet1/5', 'ifPhysAddress': 'f8:e5:7e:17:07:a8'}
        self.assertEqual(
            resolve_interface_name(details, self._existing(), self._by_mac()),
            'Ethernet1/5')

    def test_missing_if_name_is_skipped(self):
        self.assertIsNone(
            resolve_interface_name({'ifPhysAddress': 'f8:e5:7e:17:07:a5'},
                                   self._existing(), self._by_mac()))

    def test_ambiguous_mac_is_not_used(self):
        # Subinterfaces share their parent's MAC on routers; picking one of
        # several would silently update the wrong port.
        shared = 'f8:e5:7e:17:07:a5'
        sub = Interface.objects.create(
            device=self.device, name='Ethernet1/2.100',
            type=InterfaceTypeChoices.TYPE_VIRTUAL)
        sub.set_primary_mac_address_from_value(shared)
        sub.save()

        self.assertNotIn(shared.upper(), index_interfaces_by_mac(self._existing().values()))
        self.assertIsNone(
            resolve_interface_name({'ifName': 'inside', 'ifPhysAddress': shared},
                                   self._existing(), self._by_mac()))

    def test_interface_without_a_mac_is_not_indexed(self):
        Interface.objects.create(
            device=self.device, name='Ethernet1/7',
            type=InterfaceTypeChoices.TYPE_1GE_FIXED)
        self.assertNotIn('ETH', index_interfaces_by_mac(self._existing().values()))
        self.assertEqual(len(index_interfaces_by_mac(self._existing().values())), 1)
