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

from dcim.choices import InterfaceTypeChoices

from sidekick.management.commands.update_interfaces import (
    SIGNED_BIGINT_MAX,
    interface_enabled,
    interface_type_from_speed,
    sanitize_counter,
)


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
