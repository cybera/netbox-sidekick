"""Billing is cap times rate, with a UI-configurable rate and per-member override.

The rules under test, in the order they matter:

- A member override beats the global default. That is the whole point of the model:
  AHS at $0.65 must not be priced at the standard rate by accident.
- Among rows of the same kind, the most recent effective date wins, so a rate change
  is a new row rather than an edit, and a past bill stays reproducible.
- A row dated in the future does not apply yet.
- With no configured rate the resolver falls back to a constant **and says so**, so a
  caller cannot mistake an unconfigured database for a negotiated rate.
- The billable quantity is the sum of the member's current billable caps, because a
  member can have more than one accounting profile.
"""

from datetime import timedelta
from decimal import Decimal

from django.test import TestCase
from django.utils import timezone

from sidekick.utils.billing import (
    FALLBACK_RATE_PER_MBIT,
    billable_caps,
    member_billing,
    resolve_transit_rate,
)

from tenancy.models import Tenant

from .utils import BaseTest


class MemberFixtureMixin:
    """The fixtures provide two members in the Members group (pks 1 and 2)."""

    def setUp(self):
        super().setUp()
        self.today = timezone.localdate()
        self.member = Tenant.objects.get(pk=1)
        self.other = Tenant.objects.get(pk=2)

    def _rate(self, tenant, rate, days=0):
        from sidekick.models import TransitRate
        return TransitRate.objects.create(
            tenant=tenant,
            rate_per_mbit=Decimal(rate),
            effective_date=self.today - timedelta(days=days),
        )

    def test_member_override_beats_global_default(self):
        self._rate(None, '1.2000', days=30)
        self._rate(self.member, '0.6500')

        resolved = resolve_transit_rate(self.member)

        self.assertEqual(resolved['rate_per_mbit'], Decimal('0.6500'))
        self.assertEqual(resolved['rate_source'], 'member override')

    def test_global_default_applies_without_an_override(self):
        self._rate(None, '1.2000')
        resolved = resolve_transit_rate(self.other)

        self.assertEqual(resolved['rate_per_mbit'], Decimal('1.2000'))
        self.assertEqual(resolved['rate_source'], 'global default')

    def test_most_recent_effective_row_wins(self):
        self._rate(self.member, '1.5000', days=400)
        self._rate(self.member, '0.6500', days=10)

        resolved = resolve_transit_rate(self.member)

        self.assertEqual(resolved['rate_per_mbit'], Decimal('0.6500'))

    def test_future_dated_rate_does_not_apply_yet(self):
        self._rate(None, '1.2000', days=10)
        self._rate(self.member, '0.9000', days=-5)

        resolved = resolve_transit_rate(self.member)

        self.assertEqual(resolved['rate_per_mbit'], Decimal('1.2000'))
        self.assertEqual(resolved['rate_source'], 'global default')

        soon = resolve_transit_rate(self.member, as_of=self.today + timedelta(days=10))
        self.assertEqual(soon['rate_per_mbit'], Decimal('0.9000'))

    def test_unconfigured_database_reports_the_fallback(self):
        from sidekick.models import TransitRate
        # The migration seeds a global default, so "unconfigured" means every row
        # was removed, not that the table was never populated.
        TransitRate.objects.all().delete()

        resolved = resolve_transit_rate(self.member)

        self.assertEqual(resolved['rate_per_mbit'], FALLBACK_RATE_PER_MBIT)
        self.assertEqual(resolved['rate_source'], 'fallback')
        self.assertIsNone(resolved['rate_id'])


class SeededRateTest(TestCase):
    """The data migration must leave a usable global default behind."""

    def test_migration_seeds_one_global_default(self):
        from sidekick.models import TransitRate
        globals_ = TransitRate.objects.filter(tenant__isnull=True)
        self.assertEqual(globals_.count(), 1)
        self.assertEqual(globals_.first().rate_per_mbit, Decimal('1.2000'))


class MemberBillingTest(MemberFixtureMixin, BaseTest):
    def test_bill_is_cap_times_rate(self):
        from sidekick.models import TransitRate
        profile = self.member.accountingprofile_set.first()
        self.assertIsNotNone(profile, 'fixture member has no accounting profile')
        profile.bandwidthprofile_set.all().delete()
        profile.bandwidthprofile_set.create(
            effective_date=self.today - timedelta(days=1),
            traffic_cap=1000,
            burst_limit=10,
            billable=True,
        )
        TransitRate.objects.create(
            tenant=self.member, rate_per_mbit=Decimal('0.6500'), effective_date=self.today)

        billing = member_billing(self.member)

        self.assertEqual(billing['cap_mbit'], 1000)
        self.assertEqual(billing['monthly_cost'], Decimal('650.000000'))

    def test_non_billable_and_capless_rows_are_ignored(self):
        profile = self.member.accountingprofile_set.first()
        profile.bandwidthprofile_set.all().delete()
        profile.bandwidthprofile_set.create(
            effective_date=self.today - timedelta(days=1),
            traffic_cap=500, billable=False,
        )
        profile.bandwidthprofile_set.create(
            effective_date=self.today - timedelta(days=1),
            traffic_cap=None, billable=True,
        )

        self.assertEqual(billable_caps(self.member), [])
        self.assertEqual(member_billing(self.member)['monthly_cost'], Decimal('0'))

    def test_caps_sum_across_accounting_profiles(self):
        from sidekick.models import AccountingProfile
        first = self.member.accountingprofile_set.first()
        first.bandwidthprofile_set.all().delete()
        first.bandwidthprofile_set.create(
            effective_date=self.today - timedelta(days=1), traffic_cap=4000, billable=True)
        second = AccountingProfile.objects.create(member=self.member, name='second')
        second.bandwidthprofile_set.create(
            effective_date=self.today - timedelta(days=1), traffic_cap=1000, billable=True)

        billing = member_billing(self.member)

        self.assertEqual(billing['cap_mbit'], 5000)

    def test_only_the_latest_cap_per_profile_counts(self):
        profile = self.member.accountingprofile_set.first()
        profile.bandwidthprofile_set.all().delete()
        profile.bandwidthprofile_set.create(
            effective_date=self.today - timedelta(days=400), traffic_cap=2000, billable=True)
        profile.bandwidthprofile_set.create(
            effective_date=self.today - timedelta(days=1), traffic_cap=4000, billable=True)

        self.assertEqual(member_billing(self.member)['cap_mbit'], 4000)


class MemberBillingEndpointTest(MemberFixtureMixin, BaseTest):
    """The endpoint a billing report or an MCP tool calls."""

    url = '/api/plugins/sidekick/members/{}/billing/'

    def test_billing_endpoint_reports_rate_and_source(self):
        from sidekick.models import TransitRate
        profile = self.member.accountingprofile_set.first()
        profile.bandwidthprofile_set.all().delete()
        profile.bandwidthprofile_set.create(
            effective_date=self.today - timedelta(days=1), traffic_cap=4000, billable=True)
        TransitRate.objects.create(
            tenant=self.member, rate_per_mbit=Decimal('0.6500'), effective_date=self.today)

        response = self.client.get(self.url.format(self.member.pk), **self.header)

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body['cap_mbit'], 4000)
        self.assertEqual(body['rate_per_mbit'], '0.6500')
        self.assertEqual(body['rate_source'], 'member override')
        self.assertEqual(body['monthly_cost'], '2600.00')

    def test_billing_endpoint_accepts_as_of(self):
        response = self.client.get(
            self.url.format(self.member.pk) + '?as_of=2020-01-01', **self.header)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['as_of'], '2020-01-01')

    def test_billing_endpoint_404s_for_an_unknown_member(self):
        response = self.client.get(self.url.format(999999), **self.header)
        self.assertEqual(response.status_code, 404)
