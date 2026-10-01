"""Runtime tests for the bulk import/edit/rename/delete views.

NetBox's bulk views are POST-only: ``BulkEditView.get()`` and
``BulkDeleteView.get()`` unconditionally redirect to the return URL, and the
apply step only runs when ``_apply`` (edit/rename/import) or ``_confirm``
(delete) is present in the POST body.  A GET-only test therefore proves
nothing about whether the form actually saves, so each operation below drives
the real POST path and asserts the database changed.
"""
from django.urls import reverse

from sidekick.models import LogicalSystem, NetworkService, NetworkServiceL2

from .utils import BaseTest


class BulkOperationTest(BaseTest):
    def test_bulk_edit_updates_field(self):
        resp = self.client.post(
            reverse('plugins:sidekick:networkservice_bulk_edit'),
            {'_apply': 'Apply', 'pk': ['1'], 'description': 'bulk-edited description'},
        )
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(NetworkService.objects.get(pk=1).description,
                         'bulk-edited description')

    def test_bulk_rename_updates_name(self):
        resp = self.client.post(
            reverse('plugins:sidekick:logicalsystem_bulk_rename'),
            {'_apply': 'Apply', 'pk': ['1'], 'find': 'Peering', 'replace': 'Peering Renamed'},
        )
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(LogicalSystem.objects.get(pk=1).name, 'Peering Renamed')

    def test_bulk_import_creates_object(self):
        resp = self.client.post(
            reverse('plugins:sidekick:logicalsystem_bulk_import'),
            {
                '_apply': 'Apply',
                'import_method': 'direct',
                'format': 'csv',
                'csv_delimiter': ',',
                'data': 'name,slug\nImported System,imported-system\n',
            },
        )
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(LogicalSystem.objects.filter(name='Imported System').exists())

    def test_bulk_delete_removes_object(self):
        resp = self.client.post(
            reverse('plugins:sidekick:logicalsystem_bulk_delete'),
            {'_confirm': True, 'confirm': True, 'pk': ['2']},
        )
        self.assertEqual(resp.status_code, 302)
        self.assertFalse(LogicalSystem.objects.filter(pk=2).exists())


class DetailRenderTest(BaseTest):
    """Detail pages for the models that the fixture set covers."""

    def test_networkservicel2_detail_renders(self):
        v = NetworkServiceL2.objects.get(pk=1)
        resp = self.client.get(v.get_absolute_url())
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, '300')

    def test_networkservice_detail_includes_graph_panel(self):
        # The traffic graph is injected by a PluginTemplateExtension.
        v = NetworkService.objects.get(pk=1)
        resp = self.client.get(v.get_absolute_url())
        self.assertContains(resp, 'sidekick-service-graph')

        # uPlot must be served from the plugin's own static files, not a CDN.
        self.assertContains(resp, 'sidekick/uplot/uPlot.iife.min.js')
        self.assertNotContains(resp, 'leeoniya.github.io')
