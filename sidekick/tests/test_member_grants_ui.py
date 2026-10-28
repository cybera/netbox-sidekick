"""The member page shows who may act for that member, and the groups can go.

Two things under test:

- The panel on the tenant detail page lists the entitled accounts with links to add,
  edit and delete. Management of entitlement must not require the Django admin, a shell
  or knowledge of the plugin URL space.
- `prune_member_groups` deletes the tenant-named groups that used to carry access, and
  does so safely: a dry run by default, a snapshot of what it removes, and a refusal
  while a group holds a user who has no row for that member.
"""

import json
import os
import tempfile

from django.contrib.auth.context_processors import PermWrapper
from django.core.management import call_command

from tenancy.models import Tenant
from users.models import Group, User

from sidekick.models import MemberTenant
from sidekick.template_content.tenant import TenantEntitlementsPanel

from .utils import BaseTest


class TenantEntitlementsPanelTest(BaseTest):

    def setUp(self):
        super().setUp()
        self.member = Tenant.objects.get(name='East University')
        self.account = User.objects.create(username='admin@east.example')
        self.grant = MemberTenant.objects.create(
            user=self.account, tenant=self.member, note='requested in a ticket',
        )

    def render_panel(self, tenant, perms=None):
        # The real template tag supplies the request context; perms decides whether the
        # add and edit links render, so the tests pass it explicitly.
        return TenantEntitlementsPanel({'object': tenant, 'perms': perms or []}).full_width_page()

    def test_panel_lists_the_entitled_account(self):
        html = self.render_panel(self.member)
        self.assertIn('Entitled Accounts', html)
        self.assertIn(self.account.username, html)
        self.assertIn('requested in a ticket', html)

    def test_panel_links_to_every_action(self):
        # PermWrapper is what the template context processor supplies; the panel reads
        # perms.sidekick.add_membertenant, so a plain list of permissions would not do.
        html = self.render_panel(self.member, perms=PermWrapper(self.user))
        add = f'/plugins/sidekick/member_entitlements/add/?tenant={self.member.pk}'
        self.assertIn(add, html)
        self.assertIn(f'/plugins/sidekick/member_entitlements/{self.grant.pk}/edit/', html)
        self.assertIn(f'/plugins/sidekick/member_entitlements/{self.grant.pk}/delete/', html)

    def test_member_with_no_grant_says_so(self):
        MemberTenant.objects.all().delete()
        html = self.render_panel(self.member)
        self.assertIn('No account is entitled to this member', html)

    def test_non_member_tenant_with_no_grant_renders_nothing(self):
        not_a_member = Tenant.objects.get(name='Peering Partner')
        self.assertEqual(self.render_panel(not_a_member), '')

    def test_tenant_detail_page_includes_the_panel(self):
        # Proves the extension is registered, not just that the class works.
        response = self.client.get(self.member.get_absolute_url())
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Entitled Accounts')
        self.assertContains(response, self.account.username)


class PruneMemberGroupsTest(BaseTest):

    def setUp(self):
        super().setUp()
        self.member = Tenant.objects.get(name='East University')
        self.account = User.objects.create(username='admin@east.example')
        self.tenant_group = Group.objects.create(name='East University')
        self.account.groups.add(self.tenant_group)
        self.read_only = Group.objects.get_or_create(name='read-only')[0]
        self.account.groups.add(self.read_only)
        self.unrelated = Group.objects.create(name='some other group')
        self.empty_group = Group.objects.create(name='Central School')

    def run_command(self, *args, **kwargs):
        out = []
        call_command('prune_member_groups', *args, stdout=_Collector(out), **kwargs)
        return '\n'.join(out)

    def test_dry_run_deletes_nothing(self):
        self.run_command()
        self.assertTrue(Group.objects.filter(name='East University').exists())
        self.assertTrue(Group.objects.filter(name='Central School').exists())

    def test_dry_run_names_the_groups_it_would_delete(self):
        output = self.run_command()
        self.assertIn('to delete: 2', output)
        self.assertIn('East University', output)
        self.assertIn('nothing deleted', output.lower())

    def test_apply_deletes_tenant_groups_and_keeps_the_rest(self):
        MemberTenant.objects.create(user=self.account, tenant=self.member)
        self.run_command('--apply')
        self.assertFalse(Group.objects.filter(name='East University').exists())
        self.assertFalse(Group.objects.filter(name='Central School').exists())
        self.assertTrue(Group.objects.filter(name='read-only').exists())
        self.assertTrue(Group.objects.filter(name='some other group').exists())

    def test_apply_refuses_while_a_member_has_no_grant(self):
        output = self.run_command('--apply')
        self.assertIn('Refusing to delete', output)
        self.assertTrue(Group.objects.filter(name='East University').exists())
        self.assertEqual(MemberTenant.objects.count(), 0)

    def test_force_overrides_the_refusal(self):
        self.run_command('--apply', '--force')
        self.assertFalse(Group.objects.filter(name='East University').exists())

    def test_snapshot_records_what_was_deleted(self):
        MemberTenant.objects.create(user=self.account, tenant=self.member)
        handle, path = tempfile.mkstemp(suffix='.json')
        os.close(handle)
        try:
            self.run_command('--apply', '--snapshot', path)
            with open(path) as fh:
                data = json.load(fh)
        finally:
            os.unlink(path)
        rows = {row['group']: row for row in data['groups']}
        self.assertEqual(rows['East University']['tenant'], 'East University')
        self.assertEqual(rows['East University']['users'], [self.account.username])
        self.assertIn('read-only', data['kept'])

    def test_permission_bearing_group_is_never_deleted(self):
        # A tenant could in principle be named 'read-only'; the group is kept regardless.
        Tenant.objects.create(name='read-only', group=Tenant.objects.get(name='East University').group)
        MemberTenant.objects.create(
            user=self.account, tenant=Tenant.objects.get(name='read-only'),
        )
        self.run_command('--apply')
        self.assertTrue(Group.objects.filter(name='read-only').exists())


class _Collector:
    """Minimal stdout object for call_command."""

    def __init__(self, sink):
        self.sink = sink

    def write(self, message):
        if message.strip():
            self.sink.append(message.rstrip('\n'))

    def flush(self):
        pass
