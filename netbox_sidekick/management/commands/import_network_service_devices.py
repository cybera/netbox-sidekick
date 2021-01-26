import csv

from django.core.management.base import BaseCommand

from dcim.models import Device, Interface

from netbox_sidekick.models import (
    NetworkService,
    NetworkServiceDevice,
)


class Command(BaseCommand):
    help = "Import existing network service devices"

    def add_arguments(self, parser):
        parser.add_argument(
            '--file', required=True, help='The path to the CSV file')

        parser.add_argument(
            '--dry-run', required=False, action='store_true',
            help='Perform a dry-run and make no changes')

        parser.add_argument(
            '--quiet', required=False, action='store_true',
            help='Suppress messages')

    def handle(self, *args, **options):
        quiet = options['quiet']
        dry_run = options['dry_run']

        f = options['file']
        rows = []
        with open(f) as csvfile:
            r = csv.reader(csvfile, delimiter='\t')
            for row in r:
                rows.append(row)

        for row in rows:
            (interface_id, interface_name, service_id, tagged, vlan,
             legacy_device_id, speed, mtu, duplex, ip_address, subnet_mask) = row

            # Find a matching service.
            # If one isn't found, skip.
            try:
                network_service = NetworkService.objects.get(
                    legacy_id=service_id,
                )
            except NetworkService.MultipleObjectsReturned:
                self.stdout.write(
                    f"WARNING: Multiple results found for Service {service_id}. Skipping.")
                continue
            except NetworkService.DoesNotExist:
                self.stdout.write(f"WARNING: No service found for {service_id}. Skipping.")
                continue

            # If the service isn't active, skip everything else.
            if not network_service.active:
                continue

            # Find the device of the service.
            try:
                device = Device.objects.get(custom_field_data__legacy_id=legacy_device_id)
            except Device.DoesNotExist:
                self.stdout.write(
                    f"WARNING: Unable to find device: {legacy_device_id}. Skipping.")
                continue

            # Find the interface of the service.
            if vlan != '0' and vlan != 0:
                interface_name = f"{interface_name}.{vlan}"

            try:
                interface = Interface.objects.get(
                    device=device,
                    name=interface_name,
                )
            except Interface.DoesNotExist:
                self.stdout.write(
                    f"WARNING: Unable to find interface: {device} {interface_name}. Skipping.")
                continue

            # Find an existing service device entry.
            # If one doesn't exist, create one.
            try:
                service_device = NetworkServiceDevice.objects.get(
                    legacy_id=interface_id,
                )

                changed = []
                if service_device.device != device:
                    changed.append(f"{service_device.device} => {device}")
                    service_device.device = device

                if service_device.interface != interface:
                    changed.append(f"{service_device.interface} => {interface}")
                    service_device.interface = interface

                if service_device.vlan != int(vlan):
                    changed.append(f"{service_device.vlan} => {vlan}")
                    service_device.vlan = int(vlan)

                if len(changed) > 0:
                    if dry_run:
                        self.stdout.write(f"Would have updated {service_device}: {changed}")
                    else:
                        service_device.save()
                        if not quiet:
                            self.stdout.write(f"Updated {service_device}: {changed}")

            except NetworkServiceDevice.DoesNotExist:
                service_device = NetworkServiceDevice(
                    network_service=network_service,
                    device=device,
                    interface=interface,
                    vlan=int(vlan),
                    legacy_id=interface_id,
                )

                if dry_run:
                    self.stdout.write(f"Would have created {service_device}")
                else:
                    service_device.save()
                    if not quiet:
                        self.stdout.write(f"Created {service_device}")
