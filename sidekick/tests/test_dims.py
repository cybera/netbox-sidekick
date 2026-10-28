"""The member dimension is what gives old flow records a name.

Two failure modes are worth a test each. If a member's row disappears when their service is
switched off, every query over the months before is quietly wrong, and the answer reads as
"this member had no traffic". If anything joins on the slug, renaming a member breaks the
join silently, because the slug is generated from the name.
"""

from dcim.models import Site
from tenancy.models import Tenant

from sidekick.models import MemberTenant, NetworkService, NetworkServiceType
from sidekick.tests.utils import BaseTest
from sidekick.utils.dims import build_member_rows


class MemberRowTest(BaseTest):
    def setUp(self):
        super().setUp()
        self.service_type, _ = NetworkServiceType.objects.get_or_create(
            # The builder selects on the type name, lower case, so the fixture type has to
            # be named that way to be picked up at all.
            slug='transit', defaults={'name': 'transit'},
        )
        self.tenant = Tenant.objects.get(pk=1)
        # member_site is required by the model, so the fixture site is reused.
        site = Site.objects.get(pk=1)
        self.service = NetworkService.objects.create(
            name='Transit for the fixture tenant',
            active=True,
            network_service_type=self.service_type,
            member=self.tenant,
            member_site=site,
        )

    def _rows_for(self, tenant):
        member_rows, prefix_rows = build_member_rows()
        members = [r for r in member_rows if r['member_id'] == tenant.pk]
        prefixes = [r for r in prefix_rows if r['member_id'] == tenant.pk]
        return members, prefixes

    def test_an_active_member_is_marked_active(self):
        members, _ = self._rows_for(self.tenant)
        self.assertEqual(len(members), 1)
        self.assertEqual(members[0]['active'], 1)
        self.assertEqual(members[0]['member_slug'], self.tenant.slug)

    def test_a_deactivated_member_keeps_a_row_and_is_marked_inactive(self):
        self.service.active = False
        self.service.save()
        members, _ = self._rows_for(self.tenant)
        self.assertEqual(len(members), 1, 'a member who switched off must keep a row')
        self.assertEqual(members[0]['active'], 0)
        self.assertEqual(members[0]['member_name'], self.tenant.name)

    def test_prefix_rows_carry_the_member_id(self):
        _, prefixes = self._rows_for(self.tenant)
        for row in prefixes:
            self.assertEqual(row['member_id'], self.tenant.pk)
            self.assertEqual(row['member_slug'], self.tenant.slug)

    def test_a_tenant_with_only_an_entitlement_still_gets_a_row(self):
        other = Tenant.objects.create(name='Entitled But No Service', slug='entitled-but-no-service')
        MemberTenant.objects.create(user=self.user, tenant=other)
        members, _ = self._rows_for(other)
        self.assertEqual(len(members), 1)
        self.assertEqual(members[0]['active'], 0)

    def test_the_slug_follows_the_rename_and_the_id_does_not(self):
        self.tenant.name = 'Renamed Member'
        self.tenant.slug = 'renamed-member'
        self.tenant.save()
        members, _ = self._rows_for(self.tenant)
        self.assertEqual(members[0]['member_id'], self.tenant.pk)
        self.assertEqual(members[0]['member_slug'], 'renamed-member')
