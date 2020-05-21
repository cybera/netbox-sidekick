from django.urls import reverse

from netbox_sidekick.models import (
    MemberNodeType, MemberNode,
    MemberNodeLinkType, MemberNodeLink,
)

from . import utils


class MemberTests(utils.BaseTest):
    def test_model_membernodetype_basic(self):
        v = MemberNodeType.objects.get(name='Core')
        self.assertEqual(v.slug, 'core')

    def test_model_membernode_basic(self):
        v = MemberNode.objects.get(id=1)
        self.assertEqual(v.name, 'Some NREN Calgary Core Node')
        self.assertEqual(v.owner.description, 'Cybera')

    def test_model_membernodelinktype_basic(self):
        v = MemberNodeLinkType.objects.get(name='Terrestrial fiber')
        self.assertEqual(v.slug, 'terrestrial-fiber')

    def test_model_membernodelink_basic(self):
        v = MemberNodeLink.objects.get(owner__name='Cybera')
        self.assertEqual(v.name, 'Some NREN Calgary to Some NREN Edmonton')

    def test_view_membernodetype_index(self):
        resp = self.client.get(
            reverse('plugins:netbox_sidekick:membernodetype_index'))
        self.assertContains(resp, 'Core')

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

    def test_view_membernodelinktype_index(self):
        resp = self.client.get(
            reverse('plugins:netbox_sidekick:membernodelinktype_index'))
        self.assertContains(resp, 'Terrestrial fiber')

    def test_view_membernodelinktype_detail(self):
        v = MemberNodeLinkType.objects.get(id=1)
        resp = self.client.get(v.get_absolute_url())
        self.assertContains(resp, 'Terrestrial fiber')
        self.assertContains(resp, 'Some NREN Calgary to Some NREN Edmonton')

    def test_view_membernodelink_index(self):
        resp = self.client.get(
            reverse('plugins:netbox_sidekick:membernodelink_index'))
        self.assertContains(resp, 'Some NREN Calgary to Some NREN Edmonton')

    def test_view_membernodelink_detail(self):
        v = MemberNodeLink.objects.get(owner__name='Cybera')
        resp = self.client.get(v.get_absolute_url())
        self.assertContains(resp, 'Some NREN Calgary to Some NREN Edmonton')
