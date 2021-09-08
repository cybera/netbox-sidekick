import concurrent.futures
import glob
import os

from django.core.management.base import BaseCommand

from dcim.models import Device

from sidekick.models import AccountingSource, NetworkService, NIC
from sidekick.utils import convert_rrd

METRIC_CATEGORIES = [
    'in_octets', 'out_octets',
    'in_unicast_packets', 'out_unicast_packets',
    'in_nunicast_packets', 'out_nunicast_packets',
    'in_errors', 'out_errors',
]


def handle_accounting(cmd_handler, file, out_dir):
    filename = file.split('/')[-1]
    parts = filename.split('_')
    if len(parts) != 2:
        return

    (accounting_name, accounting_destination) = parts[1].split(' -- ')
    accounting_destination = accounting_destination.replace('.rrd', '')

    try:
        accounting_source = AccountingSource.objects.get(
            name=accounting_name, destination=accounting_destination)
    except AccountingSource.DoesNotExist:
        cmd_handler.stdout.write(f"Cannot find accounting source {parts[1]}")
        return

    graphite_name = "accounting.{}.{}".format(
        accounting_source.graphite_name(),
        accounting_source.graphite_destination_name()).replace('.', '/')
    dest_dir = f"{out_dir}/{graphite_name}"

    cmd_handler.stdout.write(f"Creating {dest_dir}")
    try:
        os.makedirs(dest_dir)
    except FileExistsError:
        pass
    cmd_handler.stdout.write(f"Converting {file}")
    convert_rrd(file, dest_dir)


def handle_devices(cmd_handler, file, out_dir):
    filename = file.split('/')[-1]
    parts = filename.split('_')
    if len(parts) != 2:
        return
    device_id = parts[0].replace('deviceid', '')
    interface_name = parts[1].replace('.rrd', '')
    try:
        device = Device.objects.get(
            custom_field_data__legacy_id=device_id)
    except Device.DoesNotExist:
        cmd_handler.stdout.write(f"Device with legacy ID {device_id} not found. Skipping.")
        return

    device_name = device.name.lower().replace(' ', '_')
    interface_name = interface_name.replace('.', '_')
    dest_dir = f"{out_dir}/{device_name}/{interface_name}"

    cmd_handler.stdout.write(f"Creating {dest_dir}")
    try:
        os.makedirs(dest_dir)
    except FileExistsError:
        pass
    cmd_handler.stdout.write(f"Converting {file}")
    convert_rrd(file, dest_dir)


def handle_services(cmd_handler, file, out_dir):
    filename = file.split('/')[-1]
    parts = filename.split('_')
    if len(parts) != 3:
        return

    service_id = parts[2].split('.')[0]

    try:
        service = NetworkService.objects.get(
            active=True, legacy_id=service_id)
    except NetworkService.DoesNotExist:
        cmd_handler.stdout.write(
            f"Service with legacy ID {service_id} not found. Skipping.")
        return

    service_name = service.graphite_service_name()
    nsd = service.network_service_devices.all()
    if len(nsd) > 1:
        cmd_handler.stdout.write(
            f"Service with legacy ID {service_id} has more than one " +
            "service devices. Skipping.")
        return

    nsd = nsd[0]
    nsd_interface = nsd.get_interface_entry()
    if nsd_interface is None:
        cmd_handler.stdout.write(
            f"Service with legacy ID {service_id} has no interface. Skipipng")
        return

    nic = NIC.objects.filter(
        interface_id=nsd_interface.id).order_by('-last_updated')[0]

    graphite_name = "{}.{}.{}".format(
        service_name,
        nic.graphite_device_name(),
        nic.graphite_interface_name()).replace('.', '/')

    dest_dir = f"{out_dir}/{graphite_name}"

    cmd_handler.stdout.write(f"Creating {dest_dir}")
    try:
        os.makedirs(dest_dir)
    except FileExistsError:
        pass
    cmd_handler.stdout.write(f"Converting {file}")
    convert_rrd(file, dest_dir)


class Command(BaseCommand):
    help = "Import CMDB/NetHarbour-based RRD files into Sidekick"

    def add_arguments(self, parser):
        parser.add_argument(
            '--in-dir', required=True, help='The directory where the RRD files reside')
        parser.add_argument(
            '--out-dir', required=True, help='The directory to save the whisper files')

    def handle(self, *args, **options):
        files = glob.glob("%s/accounting/*.rrd" % (options['in_dir']))
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            for file in files:
                executor.submit(handle_accounting, self, file, options['out_dir'])

        files = glob.glob("%s/*.rrd" % (options['in_dir']))
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            for file in files:
                filename = file.split('/')[-1]
                if filename.startswith('device'):
                    executor.submit(handle_devices, self, file, options['out_dir'])
                if filename.startswith('service'):
                    executor.submit(handle_services, self, file, options['out_dir'])
