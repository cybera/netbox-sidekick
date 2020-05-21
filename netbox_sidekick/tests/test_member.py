from django.urls import reverse

from netbox_sidekick.models import (
    MemberType, Member,
)

from . import utils


class MemberTests(utils.BaseTest):
    def test_model_membertype_basic(self):
        v = MemberType.objects.get(name="Post-Secondary Institution")
        self.assertEqual(v.slug, "post-secondary-institution")

    def test_model_membertype_member_count(self):
        v = MemberType.objects.get(name="Post-Secondary Institution")
        self.assertEqual(v.member_count, 1)

    def test_model_member_basic(self):
        v = Member.objects.get(tenant__name='East University')
        self.assertEqual(v.member_type.name, 'Post-Secondary Institution')

    def test_view_membertype_index(self):
        resp = self.client.get(
            reverse('plugins:netbox_sidekick:membertype_index'))
        self.assertContains(resp, 'Post-Secondary')
        # Member count
        self.assertContains(resp, '<td >1</td>')

    def test_view_membertype_index_sort(self):
        resp = self.client.get(
            reverse('plugins:netbox_sidekick:membertype_index') + "?sort=members")
        self.assertContains(resp, 'Post-Secondary')
        # Member count
        self.assertContains(resp, '<td >1</td>')

    def test_view_membertype_detail(self):
        v = MemberType.objects.get(id=1)
        resp = self.client.get(v.get_absolute_url())
        self.assertContains(resp, 'Post-Secondary')
        self.assertContains(resp, 'East University')

    def test_view_member_index(self):
        resp = self.client.get(
            reverse('plugins:netbox_sidekick:member_index'))
        self.assertContains(resp, 'East University')

    def test_view_member_index_sort(self):
        resp = self.client.get(
            reverse('plugins:netbox_sidekick:member_index') + "?sort=member")
        self.assertContains(resp, 'East University')

    def test_view_member_index_filter(self):
        resp = self.client.get(
            reverse('plugins:netbox_sidekick:member_index') + "?q=East")
        self.assertContains(resp, 'East University')

    def test_view_member_detail(self):
        v = Member.objects.get(id=1)
        resp = self.client.get(v.get_absolute_url())
        self.assertContains(resp, 'Doe, Jane')
        self.assertContains(resp, 'Doe, John')
        self.assertContains(resp, 'East University')
        self.assertContains(resp, "East University&#x27;s peering service")
        self.assertContains(resp, "East University Node")
        self.assertContains(resp, "East University Link")

    def test_api_member_list_basic(self):
        url = reverse('plugins-api:netbox_sidekick-api:member-list')
        resp = self.client.get(url, **self.header)
        self.assertEqual(resp.data['count'], 3)
        self.assertEqual(resp.data['results'][0]['tenant'], 'Central School')
        self.assertEqual(resp.data['results'][0]['member_type'], 'K-12 School Districts')
        self.assertEqual(resp.data['results'][0]['active'], True)

    def test_api_member_detail_basic(self):
        url = reverse('plugins-api:netbox_sidekick-api:member-detail', kwargs={'pk': 1})
        resp = self.client.get(url, **self.header)
        self.assertEqual(resp.data['active'], True)
        self.assertEqual(resp.data['tenant'], "East University")
        self.assertEqual(resp.data['member_type'], 'Post-Secondary Institution')
