from django.urls import reverse

from sidekick.models import (
    ContactType, Contact,
)

from . import utils


class ContactTests(utils.BaseTest):
    def test_model_contacttype_basic(self):
        v = ContactType.objects.get(name='Billing')
        self.assertEqual(v.slug, 'billing')

    def test_model_contact_basic(self):
        v = Contact.objects.get(first_name='John')
        self.assertEqual(v.last_name, 'Doe')

    def test_view_contacttype_index(self):
        resp = self.client.get(
            reverse('plugins:sidekick:contacttype_index'))
        self.assertContains(resp, 'Billing')

    def test_view_contacttype_index_sort(self):
        resp = self.client.get(
            reverse('plugins:sidekick:contacttype_index') + "?sort=name")
        self.assertContains(resp, 'Billing')

    def test_view_contacttype_detail(self):
        v = ContactType.objects.get(id=1)
        resp = self.client.get(v.get_absolute_url())
        self.assertContains(resp, 'Billing')

    def test_view_contact_index(self):
        resp = self.client.get(
            reverse('plugins:sidekick:contact_index'))
        self.assertContains(resp, 'Doe, John')

    def test_view_contact_index_filter(self):
        resp = self.client.get(
            reverse('plugins:sidekick:contact_index') + "?member=2")
        self.assertContains(resp, 'Smith, Joe')

    def test_view_contact_index_sort(self):
        resp = self.client.get(
            reverse('plugins:sidekick:contact_index') + "?sort=name")
        self.assertContains(resp, 'Doe, John')

    def test_view_contact_detail(self):
        v = Contact.objects.get(id=1)
        resp = self.client.get(v.get_absolute_url())
        self.assertContains(resp, 'Superintendent')
