from django.urls import reverse

from sidekick.models import (
    NIC
)

from .utils import BaseTest


class NICTest(BaseTest):
    def test_nic_basic(self):
        v = NIC.objects.get(id=1)
        self.assertEqual(v.admin_status, True)

    def test_view_nic_list(self):
        resp = self.client.get(
            reverse('plugins:sidekick:nic_list'))
        self.assertContains(resp, 'xe-3/3/3')

    def test_view_nic_detail(self):
        v = NIC.objects.get(id=1)
        resp = self.client.get(v.get_absolute_url())
        self.assertContains(resp, 'xe-3/3/3')

    def test_api_nic_list_basic(self):
        url = reverse('plugins-api:sidekick-api:nic_list_by_device', kwargs={'device': 1})
        resp = self.client.get(url, **self.header)
        r = resp.json()
        self.assertEqual(r[0]['admin_status'], True)
