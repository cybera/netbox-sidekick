from django.urls import reverse

from netbox_sidekick.models import MemberNodeLinkType, MemberNodeLink

from . import utils


class MemberTests(utils.BaseTest):
    def test_model_membernodelinktype_basic(self):
        v = MemberNodeLinkType.objects.get(name='Terrestrial fiber')
        self.assertEqual(v.slug, 'terrestrial-fiber')

    def test_model_membernodelinktype_membernodelink_count(self):
        v = MemberNodeLinkType.objects.get(name='Terrestrial fiber')
        self.assertEqual(v.member_node_link_count, 2)

    def test_model_membernodelink_basic(self):
        v = MemberNodeLink.objects.get(owner__tenant__name='Cybera')
        self.assertEqual(v.name, 'Some NREN Calgary to Some NREN Edmonton')

    def test_view_membernodelinktype_index(self):
        resp = self.client.get(
            reverse('plugins:netbox_sidekick:membernodelinktype_index'))
        self.assertContains(resp, 'Terrestrial fiber')
        # Member Node Link count
        self.assertContains(resp, '<td >2</td>')

    def test_view_membernodelinktype_index_sort(self):
        resp = self.client.get(
            reverse('plugins:netbox_sidekick:membernodelinktype_index') + "?sort=links")
        self.assertContains(resp, 'Terrestrial fiber')
        # Member Node Link count
        self.assertContains(resp, '<td >2</td>')

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
        v = MemberNodeLink.objects.get(owner__tenant__name='Cybera')
        resp = self.client.get(v.get_absolute_url())
        self.assertContains(resp, 'Some NREN Calgary to Some NREN Edmonton')
