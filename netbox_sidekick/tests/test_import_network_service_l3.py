import os

from io import StringIO

from django.core.management import call_command

from dcim.models import Device

from . import utils


class ImportNetworkServiceL3Test(utils.BaseTest):
    def setUp(self):
        # First import the network services
        dir_path = os.path.dirname(os.path.realpath(__file__))
        csv = f"{dir_path}/../fixtures/network-services.csv"
        out = StringIO()
        call_command('import_network_services', stdout=out, file=csv)

        csv = f"{dir_path}/../fixtures/network-service-devices.csv"
        out = StringIO()
        call_command('import_network_service_devices', stdout=out, file=csv)

        # Add legacy IDs to the devices
        for i in Device.objects.all():
            i.cf['legacy_id'] = f"{i.id}"
            i.save()

    def test_dry_run(self):
        dir_path = os.path.dirname(os.path.realpath(__file__))
        csv = f"{dir_path}/../fixtures/network-service-l3.csv"
        out = StringIO()
        call_command('import_network_service_l3', stdout=out, file=csv, dry_run=True)

        self.assertIn("Would have created logical system: C-All", out.getvalue())
        self.assertIn("Would have created logical system: Research", out.getvalue())
        self.assertIn("Would have updated East University's peering service on Router 1 xe-3/3/3.300 L3 Service", out.getvalue())
        self.assertIn("Would have created East University's peering service on Router 1 xe-3/3/3.300 L3 Service", out.getvalue())

    def test_import(self):
        dir_path = os.path.dirname(os.path.realpath(__file__))
        csv = f"{dir_path}/../fixtures/network-service-l3.csv"
        out = StringIO()
        call_command('import_network_service_l3', stdout=out, file=csv)

        self.assertIn("Created logical system: C-All", out.getvalue())
        self.assertIn("Created logical system: Research", out.getvalue())
        self.assertIn("Updated East University's peering service on Router 1 xe-3/3/3.300 L3 Service", out.getvalue())
        self.assertIn("Created East University's peering service on Router 1 xe-3/3/3.300 L3 Service", out.getvalue())
