import glob
import os
import time
import whisper

from django.core.management.base import BaseCommand

from dcim.models import Device

from sidekick.utils import parse_rrd


class Command(BaseCommand):
    help = "Update CMDB/NetHarbour-based RRD files into Sidekick"

    def add_arguments(self, parser):
        parser.add_argument(
            '--in-dir', required=True, help='The directory where the RRD files reside')
        parser.add_argument(
            '--out-dir', required=True, help='The directory to save the whisper files')

    def handle(self, *args, **options):
        now = time.time()
        files = glob.glob("%s/device*.rrd" % (options['in_dir']))
        for file in files:
            if os.stat(file).st_ctime < now - 1 * 86400:
                continue

            filename = file.split('/')[-1]
            if not filename.startswith('device'):
                continue

            parts = filename.split('_')
            if len(parts) != 2:
                continue

            device_id = parts[0].replace('deviceid', '')
            interface_name = parts[1].replace('.rrd', '')

            try:
                device = Device.objects.get(
                    custom_field_data__legacy_id=device_id)
            except Device.DoesNotExist:
                self.stdout.write(f"Device with legacy ID {device_id} not found. Skipping.")
                continue

            device_name = device.name.lower().replace(' ', '_')
            interface_name = interface_name.replace('.', '_')
            dest_dir = f"{options['out_dir']}/{device_name}/{interface_name}"

            rrd_data = parse_rrd(file)

            try:
                os.makedirs(dest_dir)
            except FileExistsError:
                pass

            for datasource, datapoints in rrd_data.items():
                # print(datapoints)
                dest_path = f"{dest_dir}/{datasource}.wsp"
                self.stdout.write(f"Creating {dest_path}")
                p1 = whisper.parseRetentionDef('5m:5y')
                p2 = whisper.parseRetentionDef('1h:10y')
                if 'octets' not in datasource:
                    p1 = whisper.parseRetentionDef('5m:1y')
                whisper.create(dest_path, [p1, p2])
                whisper.update_many(dest_path, datapoints)
