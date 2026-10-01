"""URL resolution smoke tests for the registered plugin views.

These guard against a model whose views were not registered (or whose
``get_model_urls`` wiring was dropped), which would otherwise only surface as a
NoReverseMatch when a table or panel tries to link to the object.
"""
from django.urls import NoReverseMatch, reverse
from django.test import SimpleTestCase

MODELS = (
    'logicalsystem',
    'routingtype',
    'networkservicetype',
    'networkservice',
    'networkservicedevice',
    'networkservicel2',
    'networkservicel3',
    'networkservicegroup',
    'accountingsource',
    'accountingprofile',
    'bandwidthprofile',
    'nic',
)

# NIC has no dedicated detail view (rendered on dcim.Interface).
MODELS_WITHOUT_DETAIL = ('nic',)


class URLResolutionTest(SimpleTestCase):
    def test_list_and_edit_urls(self):
        for model in MODELS:
            for suffix in ('_list', '_add'):
                name = 'plugins:sidekick:' + model + suffix
                with self.subTest(name=name):
                    self.assertTrue(reverse(name).startswith('/plugins/sidekick/'))

            for suffix in ('_edit', '_delete'):
                name = 'plugins:sidekick:' + model + suffix
                with self.subTest(name=name):
                    self.assertTrue(reverse(name, kwargs={'pk': 1}))

    def test_detail_urls(self):
        for model in MODELS:
            name = 'plugins:sidekick:' + model
            if model in MODELS_WITHOUT_DETAIL:
                with self.subTest(name=name):
                    with self.assertRaises(NoReverseMatch):
                        reverse(name, kwargs={'pk': 1})
                continue
            with self.subTest(name=name):
                self.assertTrue(reverse(name, kwargs={'pk': 1}))

    def test_custom_urls(self):
        names = (
            'plugins:sidekick:peeringconnection_list',
            'plugins:sidekick:memberbandwidth_index',
            'plugins:sidekick:membercontact_list',
        )
        for name in names:
            with self.subTest(name=name):
                self.assertTrue(reverse(name))

        for name in (
            'plugins:sidekick:memberbandwidth_detail',
            'plugins:sidekick:memberbandwidth_data',
            'plugins:sidekick:network_service_graphite_data',
            'plugins:sidekick:networkservicegroup_data',
            'plugins:sidekick:nic_graphite_data',
        ):
            with self.subTest(name=name):
                self.assertTrue(reverse(name, kwargs={'pk': 1}))
