"""Render every sidekick UI page as a superuser and insist on HTTP 200.

The filterset form used NetBox 3.x-style `(name, fields)` tuples where NetBox 4.7 wants
`FieldSet` objects. Nothing noticed: the API tests are JSON, the model form was already
correct, and the detail and edit pages worked. Only the filtered list page returned 500,
which is the page a person opens first. A reverse-url test resolves the path without
rendering it, so it passed too.

These tests render. A page that raises is a page that renders a 500.
"""

from django.contrib.auth import get_user_model
from django.test import Client
from django.urls import reverse
from tenancy.models import Tenant

from sidekick.models import MemberTenant

from .utils import BaseTest

# Every model that has a UI, with the app label NetBox needs for the route name.
UI_MODELS = (
    'logicalsystem', 'routingtype', 'networkservicetype', 'networkservice',
    'networkservicedevice', 'networkservicel2', 'networkservicel3',
    'networkservicegroup', 'accountingsource', 'accountingprofile',
    'bandwidthprofile', 'transitrate', 'nic',
)


class PluginPageRendersTest(BaseTest):

    def setUp(self):
        super().setUp()
        self.client = Client()
        self.client.force_login(self.user)

    def test_every_list_page_renders(self):
        paths = [reverse('plugins:sidekick:' + model + '_list') for model in UI_MODELS]
        for path in sorted(set(paths)):
            with self.subTest(path=path):
                response = self.client.get(path)
                self.assertEqual(response.status_code, 200, f'{path} did not render')

    def test_every_add_page_renders(self):
        for model in UI_MODELS:
            path = reverse('plugins:sidekick:' + model + '_add')
            with self.subTest(path=path):
                response = self.client.get(path)
                self.assertEqual(response.status_code, 200, f'{path} did not render')

    def test_member_access_pages_render(self):
        member = self.tenant('East University')
        account = get_user_model().objects.create(username='admin@east.example')
        grant = MemberTenant.objects.create(user=account, tenant=member)

        paths = [
            reverse('plugins:sidekick:membertenant_list'),
            reverse('plugins:sidekick:membertenant_add'),
            reverse('plugins:sidekick:membertenant', args=[grant.pk]),
            reverse('plugins:sidekick:membertenant_edit', args=[grant.pk]),
            reverse('plugins:sidekick:membertenant_delete', args=[grant.pk]),
        ]
        for path in paths:
            with self.subTest(path=path):
                response = self.client.get(path)
                self.assertEqual(response.status_code, 200, f'{path} did not render')

    def test_member_access_list_filters(self):
        """The filter form is the part that was broken; exercise it as a user would."""
        member = self.tenant('East University')
        account = get_user_model().objects.create(username='admin@east.example')
        MemberTenant.objects.create(user=account, tenant=member)

        path = reverse('plugins:sidekick:membertenant_list')
        response = self.client.get(path, {'user_id': [account.pk], 'tenant_id': [member.pk]})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, account.username)

    def tenant(self, name):
        return Tenant.objects.get(name=name)
