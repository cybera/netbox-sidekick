"""Tests for ``configure_device``, the manage.py command that sets a device's
management address and primary IP.

The command's ``--dry-run`` used to crash whenever the address was not already in
IPAM: the ``IPAddress.DoesNotExist`` branch printed its line and never bound
``mgmt_ip``, and the next block dereferenced it (``UnboundLocalError``,
reported 2026-11-17 against ``vpn2``). Dry-run is the mode an operator is told
to use first, so it has to report every planned action and change nothing.
"""

from io import StringIO

from django.core.management import call_command

from dcim.models import Device, Interface
from ipam.models import IPAddress

from sidekick.tests.utils import BaseTest


class ConfigureDeviceTest(BaseTest):
    def setUp(self):
        super().setUp()
        self.device = Device.objects.get(pk=1)

    def _run(self, **kwargs):
        out = StringIO()
        call_command('configure_device', stdout=out, **kwargs)
        return out.getvalue()

    def test_dry_run_reports_a_new_address_without_creating_it(self):
        # The regression: this raised UnboundLocalError before.
        output = self._run(name='Router 1', ip='192.168.1.50/24', dry_run=True)

        self.assertIn('Would have created a management interface called mgmt', output)
        self.assertIn('Would have created 192.168.1.50/24', output)
        self.assertIn('Would have made 192.168.1.50/24 the primary_ip4', output)

        self.assertFalse(Interface.objects.filter(device=self.device, name='mgmt').exists())
        self.assertFalse(IPAddress.objects.filter(address__net_host='192.168.1.50').exists())
        self.assertIsNone(Device.objects.get(pk=1).primary_ip4)

    def test_dry_run_reports_an_existing_address_without_attaching_it(self):
        ip = IPAddress.objects.create(address='192.168.1.51/24')

        output = self._run(name='Router 1', ip='192.168.1.51/24', dry_run=True)

        self.assertIn('Would have assigned 192.168.1.51/24 to mgmt', output)
        self.assertIsNone(IPAddress.objects.get(pk=ip.pk).assigned_object)

    def test_apply_creates_the_interface_address_and_primary(self):
        output = self._run(name='Router 1', ip='192.168.1.52/24')

        iface = Interface.objects.get(device=self.device, name='mgmt')
        ip = IPAddress.objects.get(address__net_host='192.168.1.52')
        self.assertEqual(ip.assigned_object, iface)
        self.assertEqual(Device.objects.get(pk=1).primary_ip4, ip)
        self.assertIn('Created interface mgmt', output)

    def test_named_interface_is_used_and_no_mgmt_interface_is_invented(self):
        output = self._run(name='Router 1', ip='192.168.1.53/24',
                           interface='xe-3/3/3.300')

        ip = IPAddress.objects.get(address__net_host='192.168.1.53')
        self.assertEqual(ip.assigned_object.name, 'xe-3/3/3.300')
        self.assertFalse(Interface.objects.filter(device=self.device, name='mgmt').exists())
        self.assertEqual(Device.objects.get(pk=1).primary_ip4, ip)
        self.assertIn('xe-3/3/3.300', output)

    def test_named_interface_that_does_not_exist_changes_nothing(self):
        output = self._run(name='Router 1', ip='192.168.1.54/24', interface='Ethernet1/2')

        self.assertIn('does not exist on Router 1', output)
        self.assertFalse(IPAddress.objects.filter(address__net_host='192.168.1.54').exists())
        self.assertFalse(Interface.objects.filter(device=self.device, name='mgmt').exists())

    def test_an_address_on_another_interface_is_not_moved(self):
        other = Interface.objects.get(pk=2)
        ip = IPAddress.objects.create(address='192.168.1.55/24')
        ip.assigned_object = other
        ip.save()

        output = self._run(name='Router 1', ip='192.168.1.55/24',
                           interface='xe-3/3/3.300')

        self.assertIn('already assigned to xe-3/3/4.300', output)
        self.assertEqual(IPAddress.objects.get(pk=ip.pk).assigned_object, other)

    def test_an_unassigned_address_is_attached_to_the_named_interface(self):
        ip = IPAddress.objects.create(address='192.168.1.56/24')

        self._run(name='Router 1', ip='192.168.1.56/24', interface='xe-3/3/3.300')

        self.assertEqual(IPAddress.objects.get(pk=ip.pk).assigned_object.name, 'xe-3/3/3.300')

    def test_invalid_address_is_reported(self):
        output = self._run(name='Router 1', ip='not-an-address')

        self.assertIn('Not a valid address', output)
        self.assertFalse(Interface.objects.filter(device=self.device, name='mgmt').exists())

    def test_unknown_device_is_reported(self):
        output = self._run(name='no-such-device', ip='192.168.1.57/24')

        self.assertIn('Unable to find device: no-such-device', output)

    def test_no_ip_reports_the_current_primary(self):
        output = self._run(name='Router 1')

        self.assertIn('primary IPv4 None', output)
