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

from sidekick.management.commands.update_interfaces import (
    SIGNED_BIGINT_MAX,
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
