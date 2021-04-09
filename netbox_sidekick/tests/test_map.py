from django.urls import reverse

from . import utils


# TODO
# class MapTests(utils.BaseTest):
#     def test_api_map_basic(self):
#         url = reverse('plugins-api:netbox_sidekick-api:map-list')
#         resp = self.client.get(url, **self.header)
#         self.assertTrue('</grenml:Topology>' in resp.data)
