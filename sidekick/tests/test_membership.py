"""An entitlement is a row: who may act for which member, and in what role.

The rules under test, in the order they matter:

- A row is the only source of entitlement. Nothing is inferred from a group name, so a
  tenant rename cannot change who can see what.
- One account may hold rows for several members, which is the multi-member administrator
  the group convention could not express.
- The resolver fails closed. An unknown address, an inactive account and an account with
  no rows all produce an empty set, each with a reason that says which it was. If an
  empty answer ever became a default, one member's rows would be served to another.
- Matching is case-insensitive, because an address may be recorded in mixed case and an
  exact match would lock a real person out.
- Deleting an account or a member does not delete the access record: both foreign keys
  are PROTECT.
"""

from io import StringIO

from django.core.management import call_command
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.urls import reverse

from tenancy.models import ContactRole, Tenant
from users.models import Group, User

from sidekick.models import MemberTenant
from sidekick.utils.membership import (
    REASON_INACTIVE,
    REASON_NO_ACCOUNT,
    REASON_NO_ENTITLEMENT,
    REASON_OK,
    entitled_tenant_ids,
    resolve_entitlement,
)

from .utils import BaseTest


class MemberTenantModelTest(BaseTest):
    """The fixtures provide two members in the Members group (pks 1 and 2)."""

    def setUp(self):
        super().setUp()
        self.member = Tenant.objects.get(pk=1)
        self.other = Tenant.objects.get(pk=2)
        self.account = User.objects.create(username='someone@example.ca', email='someone@example.ca')

    def test_one_account_may_hold_several_members(self):
        MemberTenant.objects.create(user=self.account, tenant=self.member)
        MemberTenant.objects.create(user=self.account, tenant=self.other)
        self.assertEqual(MemberTenant.objects.filter(user=self.account).count(), 2)

    def test_the_same_account_and_member_cannot_be_granted_twice(self):
        MemberTenant.objects.create(user=self.account, tenant=self.member)
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                MemberTenant.objects.create(user=self.account, tenant=self.member)

    def test_role_defaults_to_viewer(self):
        row = MemberTenant.objects.create(user=self.account, tenant=self.member)
        self.assertEqual(row.role, MemberTenant.ROLE_VIEWER)

    def test_deleting_the_account_is_protected(self):
        MemberTenant.objects.create(user=self.account, tenant=self.member)
        with self.assertRaises(Exception):
            self.account.delete()

    def test_deleting_the_member_is_protected(self):
        MemberTenant.objects.create(user=self.account, tenant=self.member)
        with self.assertRaises(Exception):
            self.member.delete()

    def test_str_names_both_ends(self):
        row = MemberTenant.objects.create(user=self.account, tenant=self.member)
        self.assertIn('someone@example.ca', str(row))
        self.assertIn(self.member.name, str(row))


class ResolveEntitlementTest(BaseTest):
    def setUp(self):
        super().setUp()
        self.member = Tenant.objects.get(pk=1)
        self.other = Tenant.objects.get(pk=2)

    def test_unknown_address_resolves_to_nothing_and_says_so(self):
        result = resolve_entitlement('nobody@example.ca')
        self.assertEqual(result['tenants'], [])
        self.assertEqual(result['reason'], REASON_NO_ACCOUNT)
        self.assertIsNone(result['user'])

    def test_a_non_address_resolves_to_nothing(self):
        # A plain NetBox login such as `joe.topjian` is not a member identity.
        result = resolve_entitlement('joe.topjian')
        self.assertEqual(result['reason'], REASON_NO_ACCOUNT)

    def test_an_account_with_no_rows_is_entitled_to_nothing(self):
        User.objects.create(username='bare@example.ca', email='bare@example.ca')
        result = resolve_entitlement('bare@example.ca')
        self.assertEqual(result['tenants'], [])
        self.assertEqual(result['reason'], REASON_NO_ENTITLEMENT)

    def test_an_inactive_account_is_entitled_to_nothing_even_with_rows(self):
        account = User.objects.create(
            username='gone@example.ca', email='gone@example.ca', is_active=False)
        MemberTenant.objects.create(user=account, tenant=self.member)
        result = resolve_entitlement('gone@example.ca')
        self.assertEqual(result['tenants'], [])
        self.assertEqual(result['reason'], REASON_INACTIVE)

    def test_a_grant_resolves_to_its_member_and_role(self):
        account = User.objects.create(username='staff@member.ca', email='staff@member.ca')
        MemberTenant.objects.create(
            user=account, tenant=self.member, role=MemberTenant.ROLE_ADMIN)
        result = resolve_entitlement('staff@member.ca')
        self.assertEqual(result['reason'], REASON_OK)
        self.assertEqual([t.pk for t in result['tenants']], [self.member.pk])
        self.assertEqual(result['roles'][self.member.pk], MemberTenant.ROLE_ADMIN)

    def test_several_members_all_resolve(self):
        account = User.objects.create(username='admin@two.ca', email='admin@two.ca')
        MemberTenant.objects.create(user=account, tenant=self.member)
        MemberTenant.objects.create(user=account, tenant=self.other)
        self.assertEqual(
            sorted(entitled_tenant_ids('admin@two.ca')),
            sorted([self.member.pk, self.other.pk]),
        )

    def test_matching_is_case_insensitive(self):
        account = User.objects.create(username='Mixed.Case@Example.ca', email='Mixed.Case@Example.ca')
        MemberTenant.objects.create(user=account, tenant=self.member)
        self.assertEqual(entitled_tenant_ids('mixed.case@example.ca'), [self.member.pk])


class EntitlementAPITest(BaseTest):
    def setUp(self):
        super().setUp()
        self.member = Tenant.objects.get(pk=1)

    def test_entitlement_endpoint_reports_reason_and_members(self):
        account = User.objects.create(username='api@member.ca', email='api@member.ca')
        MemberTenant.objects.create(user=account, tenant=self.member)
        response = self.client.get(
            reverse('plugins-api:sidekick-api:member_entitlement'),
            {'address': 'api@member.ca'},
            **self.header,
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload['found'])
        self.assertEqual(payload['reason'], REASON_OK)
        self.assertEqual([t['id'] for t in payload['tenants']], [self.member.pk])
        self.assertEqual(payload['tenants'][0]['role'], MemberTenant.ROLE_VIEWER)

    def test_entitlement_endpoint_fails_closed_for_an_unknown_address(self):
        response = self.client.get(
            reverse('plugins-api:sidekick-api:member_entitlement'),
            {'address': 'nobody@example.ca'},
            **self.header,
        )
        payload = response.json()
        self.assertFalse(payload['found'])
        self.assertEqual(payload['reason'], REASON_NO_ACCOUNT)
        self.assertEqual(payload['tenants'], [])

    def test_entitlement_endpoint_requires_authentication(self):
        response = self.client.get(
            reverse('plugins-api:sidekick-api:member_entitlement'),
            {'address': 'api@member.ca'},
        )
        self.assertIn(response.status_code, (401, 403))


class BackfillCommandTest(BaseTest):
    """The command seeds rows from groups and refuses to guess what a group means."""

    def setUp(self):
        super().setUp()
        self.member = Tenant.objects.get(pk=1)
        self.account = User.objects.create(username='staff@member.ca', email='staff@member.ca')
        self.group = Group.objects.create(name=self.member.name)
        self.account.groups.add(self.group)

    def test_dry_run_writes_nothing(self):
        out = StringIO()
        call_command('member_entitlements', stdout=out)
        self.assertEqual(MemberTenant.objects.count(), 0)
        self.assertIn('Dry run', out.getvalue())
        self.assertIn('to create: 1', out.getvalue())

    def test_apply_creates_the_row_with_the_group_in_its_note(self):
        out = StringIO()
        call_command('member_entitlements', '--apply', stdout=out)
        row = MemberTenant.objects.get()
        self.assertEqual(row.user, self.account)
        self.assertEqual(row.tenant, self.member)
        self.assertIn(self.member.name, row.note)
        self.assertEqual(row.role, MemberTenant.ROLE_VIEWER)

    def test_apply_twice_is_idempotent(self):
        call_command('member_entitlements', '--apply', stdout=StringIO())
        out = StringIO()
        call_command('member_entitlements', '--apply', stdout=out)
        self.assertEqual(MemberTenant.objects.count(), 1)
        self.assertIn('to create: 0', out.getvalue())

    def test_a_group_matching_no_member_is_reported_not_invented(self):
        stray = Group.objects.create(name='read-only')
        self.account.groups.add(stray)
        out = StringIO()
        call_command('member_entitlements', '--apply', stdout=out)
        self.assertEqual(MemberTenant.objects.count(), 1)
        self.assertIn('resolve to no member', out.getvalue())
        self.assertIn('read-only', out.getvalue())

    def test_a_disabled_suffix_still_resolves(self):
        self.member.name = f'{self.member.name} - disabled'
        self.member.save()
        call_command('member_entitlements', '--apply', stdout=StringIO())
        self.assertEqual(MemberTenant.objects.filter(tenant=self.member).count(), 1)

    def test_recreate_groups_rebuilds_the_convention_from_the_rows(self):
        call_command('member_entitlements', '--apply', stdout=StringIO())
        self.group.delete()
        call_command('member_entitlements', '--recreate-groups', '--apply', stdout=StringIO())
        rebuilt = Group.objects.get(name=self.member.name)
        self.assertIn(rebuilt, self.account.groups.all())


class MemberContactsViewTest(BaseTest):
    """The contacts page lists portal accounts from the entitlement rows.

    It used to derive them from a group whose name equalled the member's, so a member
    whose group name had drifted lost its accounts from the page without any error.
    """

    def setUp(self):
        super().setUp()
        # The page filters portal accounts by the Network contact role, which it
        # creates in production and which the fixtures do not provide.
        ContactRole.objects.get_or_create(name='Network', slug='network')

    def test_an_entitled_account_appears_for_its_member(self):
        member = Tenant.objects.get(pk=1)
        account = User.objects.create(username='listed@member.ca', email='listed@member.ca')
        MemberTenant.objects.create(user=account, tenant=member)
        response = self.client.get(
            reverse('plugins:sidekick:membercontact_list'), {'member': member.pk})
        self.assertEqual(response.status_code, 200)
        listed = [row['contact'] for row in response.context['member_contacts'].data]
        self.assertIn('listed@member.ca', listed)

    def test_an_account_without_a_row_does_not_appear(self):
        member = Tenant.objects.get(pk=1)
        account = User.objects.create(username='absent@member.ca', email='absent@member.ca')
        group = Group.objects.create(name=member.name)
        account.groups.add(group)
        response = self.client.get(
            reverse('plugins:sidekick:membercontact_list'), {'member': member.pk})
        listed = [row['contact'] for row in response.context['member_contacts'].data]
        self.assertNotIn('absent@member.ca', listed)
