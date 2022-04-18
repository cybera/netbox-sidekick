from django.urls import reverse

from sidekick.models import (
    AccountingProfile,
    AccountingSource,
    BandwidthProfile,
)

from .utils import BaseTest


class AccountingTest(BaseTest):
    # Accounting Source
    def test_accountingsource_basic(self):
        v = AccountingSource.objects.get(device=1, name='Client-EastUniversity')
        self.assertEqual(v.destination, 'Primary ISP')

    def test_view_accountingsource_list(self):
        resp = self.client.get(
            reverse('plugins:sidekick:accountingsource_list'))
        self.assertContains(resp, 'Router 1')
        self.assertContains(resp, 'Router 2')
        self.assertContains(resp, 'Client-EastUniversity')

    def test_view_accountingsource_detail(self):
        v = AccountingSource.objects.get(device=1, name='Client-EastUniversity')
        resp = self.client.get(v.get_absolute_url())
        self.assertContains(resp, "Router 1: Client-EastUniversity")

    # Accounting Profile
    def test_accountingprofile_basic(self):
        v = AccountingProfile.objects.get(id=1)
        self.assertEqual(v.comments, "East University's profile")

    def test_view_accountingprofile_list(self):
        resp = self.client.get(
            reverse('plugins:sidekick:accountingprofile_list'))
        self.assertContains(resp, 'East University')

    def test_view_accountingprofile_detail(self):
        v = AccountingProfile.objects.get(id=1)
        resp = self.client.get(v.get_absolute_url())
        self.assertContains(resp, 'East University&#x27;s profile')
        self.assertContains(resp, '200000000')

    # Bandwidth Profile
    def test_bandwidthprofile_basic(self):
        v = BandwidthProfile.objects.get(id=1)
        self.assertEqual(v.traffic_cap, 200000000)

    def test_view_bandwidthprofile_list(self):
        resp = self.client.get(
            reverse('plugins:sidekick:bandwidthprofile_list'))
        self.assertContains(resp, 'East University')
        self.assertContains(resp, '200000000')
