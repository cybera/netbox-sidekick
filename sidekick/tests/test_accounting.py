from django.urls import reverse

from sidekick.models import (
    AccountingProfile,
    AccountingClass,
    BandwidthProfile,
)

from .utils import BaseTest


class AccountingTest(BaseTest):
    # Accounting Class
    def test_accountingclass_basic(self):
        v = AccountingClass.objects.get(device=1, name='Client-EastUniversity')
        self.assertEqual(v.destination, 'Primary ISP')

    def test_view_accountingclass_index(self):
        resp = self.client.get(
            reverse('plugins:sidekick:accountingclass_index'))
        self.assertContains(resp, 'Router 1')
        self.assertContains(resp, 'Router 2')
        self.assertContains(resp, 'Client-EastUniversity')

    def test_view_accountingclass_detail(self):
        v = AccountingClass.objects.get(device=1, name='Client-EastUniversity')
        resp = self.client.get(v.get_absolute_url())
        self.assertContains(resp, "Router 1: Client-EastUniversity")

    # Accounting Profile
    def test_accountingprofile_basic(self):
        v = AccountingProfile.objects.get(id=1)
        self.assertEqual(v.comments, "East University's profile")

    def test_view_accountingprofile_index(self):
        resp = self.client.get(
            reverse('plugins:sidekick:accountingprofile_index'))
        self.assertContains(resp, 'East University')

    def test_view_accountingprofile_detail(self):
        v = AccountingProfile.objects.get(id=1)
        resp = self.client.get(v.get_absolute_url())
        self.assertContains(resp, 'East University&#x27;s profile')
        self.assertContains(resp, '200000000')
        self.assertContains(resp, 'Router 1')

    # Bandwidth Profile
    def test_bandwidthprofile_basic(self):
        v = BandwidthProfile.objects.get(id=1)
        self.assertEqual(v.traffic_cap, 200000000)

    def test_view_bandwidthprofile_index(self):
        resp = self.client.get(
            reverse('plugins:sidekick:bandwidthprofile_index'))
        self.assertContains(resp, 'East University')
        self.assertContains(resp, '200000000')
