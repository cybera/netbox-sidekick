from django.urls import reverse

from netbox_sidekick.models import MemberNodeType, MemberNode

from . import utils


class MemberTests(utils.BaseTest):
    def test_model_membernodetype_basic(self):
        v = MemberNodeType.objects.get(name='Core')
        self.assertEqual(v.slug, 'core')

    def test_model_membernodetype_membernode_count(self):
        v = MemberNodeType.objects.get(name='Core')
        self.assertEqual(v.member_node_count, 2)

    def test_model_membernode_basic(self):
        v = MemberNode.objects.get(id=1)
        self.assertEqual(v.name, 'Some NREN Calgary Core Node')
        self.assertEqual(v.owner.tenant.description, 'Cybera')

    def test_view_membernodetype_index(self):
        resp = self.client.get(
            reverse('plugins:netbox_sidekick:membernodetype_index'))
        self.assertContains(resp, 'Core')
        # Member Nodes count
        self.assertContains(resp, '<td >2</td>')

    def test_view_membernodetype_index_sort(self):
        resp = self.client.get(
            reverse('plugins:netbox_sidekick:membernodetype_index') + "?sort=nodes")
        self.assertContains(resp, 'Core')
        # Member Nodes count
        self.assertContains(resp, '<td >2</td>')

    def test_view_membernodetypedetail(self):
        v = MemberNode.objects.get(id=1)
        resp = self.client.get(v.get_absolute_url())
        self.assertContains(resp, 'Core')
        self.assertContains(resp, 'Calgary Core Node')

    def test_view_membernode_index(self):
        resp = self.client.get(
            reverse('plugins:netbox_sidekick:membernode_index'))
        self.assertContains(resp, 'Calgary Core Node')

    def test_view_membernode_detail(self):
        v = MemberNode.objects.get(id=1)
        resp = self.client.get(v.get_absolute_url())
        self.assertContains(resp, 'Calgary Core Node')
