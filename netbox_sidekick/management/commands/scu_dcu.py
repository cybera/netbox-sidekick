from django.conf import settings
from django.core.management.base import BaseCommand

from dcim.models import (
    Device
)

from netbox_sidekick.utils import (
    decrypt_secret,
    snmpwalk_bulk_accounting,
)


class Command(BaseCommand):
    help = "Update SCU/DCU Accounting Data"

    def add_arguments(self, parser):
        parser.add_argument(
            '--device-name', required=True, help='The name of the device')

        parser.add_argument(
            '--dry-run', required=False, action='store_true',
            help='Perform a dry-run and make no changes')

    def handle(self, *args, **options):
        # First, query for the device by name.
        try:
            device = Device.objects.get(name=options['device_name'])
        except Device.DoesNotExist:
            self.stdout.write(f"Unable to find device: {options['device_name']}")
            return

        # Determine the information needed to connect to the device.
        mgmt_ip = device.primary_ip4
        secret_username = settings.PLUGINS_CONFIG['netbox_sidekick'].get('secret_user', None)
        private_key_path = settings.PLUGINS_CONFIG['netbox_sidekick'].get('secret_private_key_path', None)

        # If all of the connection information was found,
        # attempt to decrypt the connection credentials,
        # connect to the device, and inventory the interfaces.
        if mgmt_ip is not None and \
           secret_username is not None and \
           private_key_path is not None:

            _mgmt_ip = "%s" % (mgmt_ip.address.ip)

            try:
                snmp = decrypt_secret(device, 'snmp', secret_username, private_key_path)
            except Exception as e:
                self.stdout.write(f"Unable to decrypt snmp secret: {e}")

            if snmp is None:
                self.stdout.write(f"Unable to find snmp secret for {device}")
                return

            try:
                results = snmpwalk_bulk_accounting(_mgmt_ip, snmp)
            except Exception as e:
                self.stdout.write(f"Error querying device {device}: {e}")
                return

            customer_names = results['customer_names']
            isps = results['isps']
            scu_bytes = results['scu_bytes']
            dcu_bytes = results['dcu_bytes']

            profiles = {}
            current = {}

            for k, v in scu_bytes.items():
                for isp, data in v.items():
                    title = f"{customer_names[k]} -- {isps[isp]}"
                    if title not in profiles:
                        profiles[title] = {}
                        profiles[title]['customer'] = customer_names[k]
                        profiles[title]['isp'] = isps[isp]
                        profiles[title]['device'] = device.name
                    if title not in current:
                        current[title] = {}
                    current[title]['scu'] = data

                    self.stdout.write(f"{title}: {data}")

            for k, v in dcu_bytes.items():
                for isp, data in v.items():
                    title = f"{customer_names[k]} -- {isps[isp]}"
                    if title not in profiles:
                        profiles[title] = {}
                        profiles[title]['customer'] = customer_names[k]
                        profiles[title]['isp'] = isps[isp]
                        profiles[title]['device'] = device.name

                    if title not in current:
                        current[title] = {}
                    current[title]['dcu'] = data

            for customer, data in current.items():
                self.stdout.write(f"{customer}: {data}")
