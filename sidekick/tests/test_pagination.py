"""Guard against API list endpoints that break under NetBox 4.x pagination.

NetBox 4.x paginates through ``OptionalLimitOffsetPagination``, which raises
``QuerySetNotOrdered`` (HTTP 500) for any queryset whose model has no
``Meta.ordering`` and whose viewset does not apply ``order_by``::

    "Paginating over an unordered queryset is unreliable."

This is not hypothetical: the 2026-10-04 failure of the netflow-host ASN
import cron (import_subnets_clickhouse.py) was exactly this —
GET /api/plugins/sidekick/networkservicel3/?limit=1000 returned 500 on
NetBox 4.7 because NetworkServiceL3 had no Meta.ordering.

These tests hit every paginated plugin list endpoint the cron jobs and
integrations actually call, with the same ``limit`` parameter, and assert
the response is 200 rather than a 500.
"""

from django.urls import reverse
from rest_framework import status

from .utils import BaseTest


class APIPaginationTest(BaseTest):
    def _assert_list_ok(self, endpoint, query=''):
        url = reverse('plugins-api:sidekick-api:%s-list' % endpoint)
        resp = self.client.get(url + query, **self.header)
        self.assertEqual(
            resp.status_code, status.HTTP_200_OK,
            msg='GET %s%s -> %s: %s' % (url, query, resp.status_code,
                                        getattr(resp, 'data', resp.content)),
        )
        return resp.data

    def test_networkservicel3_list_paginates(self):
        data = self._assert_list_ok('networkservicel3', '?limit=1000')
        self.assertGreater(data['count'], 0)

    def test_networkservicel2_list_paginates(self):
        data = self._assert_list_ok('networkservicel2', '?limit=1000')
        self.assertGreater(data['count'], 0)

    def test_networkservicedevice_list_paginates(self):
        data = self._assert_list_ok('networkservicedevice', '?limit=1000')
        self.assertGreater(data['count'], 0)

    def test_networkservice_list_paginates(self):
        self._assert_list_ok('networkservice', '?limit=1000')

    def test_accountingsource_list_paginates(self):
        self._assert_list_ok('accountingsource', '?limit=1000')

    def test_accountingprofile_list_paginates(self):
        self._assert_list_ok('accountingprofile', '?limit=1000')

    def test_bandwidthprofile_list_paginates(self):
        self._assert_list_ok('bandwidthprofile', '?limit=1000')

    def test_logicalsystem_list_paginates(self):
        self._assert_list_ok('logicalsystem', '?limit=1000')

    def test_routingtype_list_paginates(self):
        self._assert_list_ok('routingtype', '?limit=1000')

    def test_networkservicetype_list_paginates(self):
        self._assert_list_ok('networkservicetype', '?limit=1000')

    def test_networkservicegroup_list_paginates(self):
        self._assert_list_ok('networkservicegroup', '?limit=1000')
