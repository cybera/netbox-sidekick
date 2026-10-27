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
- The UI edits a row's member and nothing else. A different price or start date is a new
  row, created by cloning the old one, so a past bill cannot be rewritten by an edit.
"""

import re
from datetime import timedelta
from decimal import Decimal

from django.test import TestCase
from django.urls import NoReverseMatch, reverse
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


class TransitRateEditUITest(BaseTest):
    """A rate row is history. The UI must not let an edit rewrite it.

    Correcting the member a row is attached to is the one safe in-place change, because
    the price and the date keep their meaning. A different price or start date is a new
    row, created by cloning the old one. Deliberately not built on MemberFixtureMixin:
    that mixin carries the rate-resolution tests, which this class's own rows would
    disturb.
    """

    def setUp(self):
        super().setUp()
        from sidekick.models import TransitRate
        self.today = timezone.localdate()
        self.member = Tenant.objects.get(pk=1)
        self.other = Tenant.objects.get(pk=2)
        self.rate = TransitRate.objects.create(
            tenant=self.member,
            rate_per_mbit=Decimal('0.6500'),
            effective_date=self.today - timedelta(days=30),
            comments='agreed for the term',
        )
        self.edit_url = reverse('plugins:sidekick:transitrate_edit', args=[self.rate.pk])

    def _field_tag(self, html, name):
        match = re.search(r'<(?:input|select|textarea)[^>]*name="%s"[^>]*>' % name, html)
        self.assertIsNotNone(match, f'{name} is not on the page')
        return match.group(0)

    def test_edit_page_prefills_the_row(self):
        response = self.client.get(self.edit_url)

        self.assertEqual(response.status_code, 200)
        form = response.context['form']
        self.assertEqual(form.instance.pk, self.rate.pk)
        self.assertEqual(form['tenant'].value(), self.member.pk)
        self.assertEqual(form['rate_per_mbit'].value(), Decimal('0.6500'))
        self.assertEqual(form['effective_date'].value(), self.rate.effective_date)

    def test_edit_page_locks_price_date_and_comments(self):
        html = self.client.get(self.edit_url).content.decode()

        for name in ('rate_per_mbit', 'effective_date', 'comments'):
            with self.subTest(field=name):
                self.assertIn('disabled', self._field_tag(html, name))
        self.assertNotIn('disabled', self._field_tag(html, 'tenant'))

    def test_add_page_accepts_all_fields(self):
        html = self.client.get(reverse('plugins:sidekick:transitrate_add')).content.decode()

        for name in ('rate_per_mbit', 'effective_date', 'comments', 'tenant'):
            with self.subTest(field=name):
                self.assertNotIn('disabled', self._field_tag(html, name))

    def test_a_tampered_post_cannot_change_the_price_or_date(self):
        response = self.client.post(self.edit_url, {
            'tenant': self.other.pk,
            'rate_per_mbit': '9.9999',
            'effective_date': '2020-01-01',
            'comments': 'rewritten',
        })

        self.assertEqual(response.status_code, 302)
        self.rate.refresh_from_db()
        self.assertEqual(self.rate.tenant, self.other)
        self.assertEqual(self.rate.rate_per_mbit, Decimal('0.6500'))
        self.assertEqual(self.rate.effective_date, self.today - timedelta(days=30))
        self.assertEqual(self.rate.comments, 'agreed for the term')

    def test_clearing_the_member_makes_the_row_the_global_default(self):
        response = self.client.post(self.edit_url, {'tenant': ''})

        self.assertEqual(response.status_code, 302)
        self.rate.refresh_from_db()
        self.assertIsNone(self.rate.tenant_id)

    def test_bulk_edit_url_is_not_registered(self):
        with self.assertRaises(NoReverseMatch):
            reverse('plugins:sidekick:transitrate_bulk_edit')

    def test_list_page_offers_no_bulk_edit(self):
        html = self.client.get(reverse('plugins:sidekick:transitrate_list')).content.decode()

        self.assertNotIn('Edit Selected', html)
        self.assertNotIn('name="_edit"', html)

    def test_clone_prefills_the_new_row_for_a_superseding_rate(self):
        response = self.client.get(
            reverse('plugins:sidekick:transitrate_add'),
            {'tenant': self.member.pk, 'rate_per_mbit': '0.6500', 'effective_date': '2027-01-01'},
        )

        self.assertEqual(response.status_code, 200)
        form = response.context['form']
        self.assertIsNone(form.instance.pk, 'cloning must build a new row, not edit the old one')
        self.assertEqual(form['rate_per_mbit'].value(), '0.6500')
        self.assertNotIn('disabled', self._field_tag(response.content.decode(), 'rate_per_mbit'))
