from django.urls import reverse

from netbox_sidekick.models import (
    MemberType, Member,
)

from . import utils


class MemberTests(utils.BaseTest):
    def test_model_membertype_basic(self):
        v = MemberType.objects.get(name="Post-Secondary Institution")
        self.assertEqual(v.slug, "post-secondary-institution")

    def test_model_member_basic(self):
        v = Member.objects.get(tenant__name='East University')
        self.assertEqual(v.member_type.name, 'Post-Secondary Institution')

    def test_view_membertype_index(self):
        resp = self.client.get(
            reverse('plugins:netbox_sidekick:membertype_index'))
        self.assertContains(resp, 'Post-Secondary')

    def test_view_membertype_detail(self):
        v = MemberType.objects.get(id=1)
        resp = self.client.get(v.get_absolute_url())
        self.assertContains(resp, 'Post-Secondary')
        self.assertContains(resp, 'East University')

    def test_view_member_index(self):
        resp = self.client.get(
            reverse('plugins:netbox_sidekick:member_index'))
        self.assertContains(resp, 'East University')

    def test_view_member_detail(self):
        v = Member.objects.get(id=1)
        resp = self.client.get(v.get_absolute_url())
        self.assertContains(resp, 'East University')
        self.assertContains(resp, "East University&#x27;s peering service")
