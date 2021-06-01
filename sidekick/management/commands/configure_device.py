from django.core.management.base import BaseCommand

from dcim.choices import InterfaceTypeChoices
from dcim.models import Device, Interface

from ipam.models import IPAddress


class Command(BaseCommand):
    help = "Import device information"

    def add_arguments(self, parser):
        parser.add_argument(
            '--name', required=True, help='The name of the device')

        parser.add_argument(
            '--ip', required=False, help='The management IP of the device')

        parser.add_argument(
            '--dry-run', required=False, action='store_true',
            help='Perform a dry-run and make no changes')

    def handle(self, *args, **options):
        # First, query for the device by name.
        try:
            device = Device.objects.get(name=options['name'])
        except Device.DoesNotExist:
            self.stdout.write(f"Unable to find device: {options['name']}")
            return

        # If an IP address was specified, then configure the device with it.
        _ip = options['ip']
        if _ip is not None:
            # Make sure there's an interface named "mgmt"
            # If there isn't, then create one.
            mgmt_iface = next((True for iface in device.vc_interfaces.all() if iface.name == 'mgmt'), None)
            if not mgmt_iface:
                if options['dry_run']:
                    self.stdout.write('Would have created a managment interface called mgmt')
                else:
                    mgmt_iface = Interface(device=device, name='mgmt', type=InterfaceTypeChoices.TYPE_VIRTUAL)
                    mgmt_iface.save()

            # Make sure the specific IP address exists and is on the mgmt interface.
            try:
                _ip = options['ip']
                mgmt_ip = IPAddress.objects.get(address=_ip)

                # If the IP exists, make sure it's currently not assigned to another interface.
                if mgmt_ip.interface is not None:
                    if mgmt_ip.interface.name != 'mgmt' and mgmt_ip.interface.device.id != device.id:
                        self.stdout.write(f"IP Address {_ip} is already assigned to {mgmt_ip.interface.device.name}")
                        return
                # Otherwise, add the IP to the interface.
                else:
                    if options['dry_run']:
                        self.stdout.write(f"Would have added {mgmt_ip} to the mgmt interface")
                    else:
                        mgmt_ip.interface = mgmt_iface
                        mgmt_ip.save()
            except IPAddress.DoesNotExist:
                # If the IP doesn't exist, create it and link it to the mgmt interfae.
                if options['dry_run']:
                    self.stdout.write(f"Would have created IP address {options['ip']} and assigned it to the mgmt interface")
                else:
                    mgmt_ip = IPAddress(address=options['ip'], interface=mgmt_iface)
                    mgmt_ip.save()

            # Ensure the primary IP address of the device is set to the mgmt IP.
            if device.primary_ip4 is None or device.primary_ip4.id != mgmt_ip.id:
                if options['dry_run']:
                    self.stdout.write(f"Would have assigned {mgmt_ip} as the primary IP of the device")
                else:
                    device.primary_ip4 = mgmt_ip
                    device.save()
