import ipaddress

from django.core.management.base import BaseCommand

from dcim.choices import InterfaceTypeChoices
from dcim.models import Device, Interface

from ipam.models import IPAddress

LEGACY_INTERFACE = 'mgmt'


class Command(BaseCommand):
    help = "Attach a device's management address to an interface and make it the primary IP"

    def add_arguments(self, parser):
        parser.add_argument(
            '--name', required=True, help='The name of the device')

        parser.add_argument(
            '--ip', required=False,
            help='Management address in CIDR form, e.g. 199.116.232.244/28')

        parser.add_argument(
            '--interface', required=False, default=None,
            help="Existing interface to attach the address to, e.g. Ethernet1/2. "
                 "Omitted: the legacy 'mgmt' interface is used, and created if the "
                 "device has none.")

        parser.add_argument(
            '--dry-run', required=False, action='store_true',
            help='Report what would change and make no changes')

    def handle(self, *args, **options):
        dry_run = options['dry_run']

        try:
            device = Device.objects.get(name=options['name'])
        except Device.DoesNotExist:
            self.stdout.write(f"Unable to find device: {options['name']}")
            return

        if options['ip'] is None:
            self.stdout.write(
                f"{device.name}: primary IPv4 {device.primary_ip4}, "
                f"primary IPv6 {device.primary_ip6}. Pass --ip to set it.")
            return

        try:
            address = ipaddress.ip_interface(options['ip'])
        except ValueError:
            self.stdout.write(
                f"Not a valid address: {options['ip']} "
                f"(expected CIDR form, e.g. 199.116.232.244/28)")
            return

        # Which interface carries the address.
        if options['interface']:
            iface = next(
                (i for i in device.vc_interfaces() if i.name == options['interface']),
                None)
            if iface is None:
                self.stdout.write(
                    f"Interface {options['interface']} does not exist on {device.name}. "
                    f"Create it in NetBox first; this command only fills in the legacy "
                    f"'{LEGACY_INTERFACE}' interface, it does not invent a named one.")
                return
        else:
            # A real interface is preferred, but most devices were documented with a
            # synthetic 'mgmt' interface holding the management address. Any interface
            # works -- update_interfaces reads device.primary_ip4, not the interface
            # name -- so this branch exists only for that convention.
            iface = next(
                (i for i in device.vc_interfaces() if i.name == LEGACY_INTERFACE),
                None)

        target_name = iface.name if iface is not None else LEGACY_INTERFACE

        # The IPAddress row, if IPAM already has it. NetBox 4 assigns an address
        # through the generic `assigned_object`; the `interface` kwarg the old code
        # used no longer exists (TypeError: Direct assignment to the reverse side of
        # a related set).
        mgmt_ip = IPAddress.objects.filter(address__net_host=str(address.ip)).first()
        if mgmt_ip is not None and mgmt_ip.assigned_object is not None:
            current = mgmt_ip.assigned_object
            # Refuse rather than move an address that belongs somewhere else: the
            # operator named an interface, or did not, and either way this command
            # should not silently steal an assignment off another device or port.
            if iface is None or current.id != iface.id:
                self.stdout.write(
                    f"{mgmt_ip.address} is already assigned to {current.name} "
                    f"on {current.device.name}")
                return

        primary_field = 'primary_ip4' if address.version == 4 else 'primary_ip6'
        primary_now = getattr(device, primary_field)

        needs_interface = iface is None
        needs_ip = mgmt_ip is None
        # -1 stands for "the interface this run will create", so an existing but
        # unassigned address is attached rather than left dangling.
        needs_attach = not needs_ip and mgmt_ip.assigned_object_id != (
            iface.id if iface is not None else -1)
        needs_primary = primary_now is None or str(primary_now.address) != str(address)

        if not (needs_interface or needs_ip or needs_attach or needs_primary):
            self.stdout.write(
                f"Nothing to do: {device.name} already has {address} on {target_name} "
                f"as its {primary_field}.")
            return

        if dry_run:
            # Every branch reports; none of them touch a variable the next one needs.
            # The command used to print the first two lines and then dereference an
            # unset mgmt_ip, so --dry-run crashed whenever the address was not yet in
            # IPAM (UnboundLocalError, 2026-11-17).
            if needs_interface:
                self.stdout.write(
                    f"Would have created a management interface called {LEGACY_INTERFACE}")
            if needs_ip:
                self.stdout.write(
                    f"Would have created {address} and assigned it to {target_name}")
            elif needs_attach:
                self.stdout.write(
                    f"Would have assigned {mgmt_ip.address} to {target_name}")
            if needs_primary:
                self.stdout.write(
                    f"Would have made {address} the {primary_field} of {device.name}")
            return

        if needs_interface:
            iface = Interface(
                device=device,
                name=LEGACY_INTERFACE,
                type=InterfaceTypeChoices.TYPE_VIRTUAL)
            iface.save()
            self.stdout.write(f"Created interface {iface.name}")

        if needs_ip:
            mgmt_ip = IPAddress(address=str(address))
            mgmt_ip.assigned_object = iface
            mgmt_ip.save()
            self.stdout.write(f"Created {mgmt_ip.address} on {iface.name}")
        elif needs_attach:
            mgmt_ip.assigned_object = iface
            mgmt_ip.save()
            self.stdout.write(f"Assigned {mgmt_ip.address} to {iface.name}")

        if needs_primary:
            setattr(device, primary_field, mgmt_ip)
            device.save()
            self.stdout.write(
                f"{mgmt_ip.address} is now the {primary_field} of {device.name}")
