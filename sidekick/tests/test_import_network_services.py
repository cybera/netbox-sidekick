from io import StringIO
from django.core.management import call_command

import os

from . import utils


class ImportNetworkServicesTest(utils.BaseTest):
    def test_dry_run(self):
        dir_path = os.path.dirname(os.path.realpath(__file__))
        csv = f"{dir_path}/../fixtures/network-services.csv"

        out = StringIO()
        call_command('import_network_services', stdout=out, file=csv, dry_run=True)

        self.assertIn('Would have created network service type: Transit', out.getvalue())
        self.assertIn('Would have created network service: Central School: Another Service Name', out.getvalue())

    def test_import(self):
        dir_path = os.path.dirname(os.path.realpath(__file__))
        csv = f"{dir_path}/../fixtures/network-services.csv"

        out = StringIO()
        call_command('import_network_services', stdout=out, file=csv)

        self.assertIn('Created network service type: Transit', out.getvalue())
        self.assertIn('Created network service: Central School: Another Service Name', out.getvalue())
