import graphyte

from django.conf import settings
from django.core.management.base import BaseCommand

from dcim.models import (
    Device
)

from sidekick.models import (
    AccountingSource,
    AccountingSourceCounter,
)

from sidekick.utils import (
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
        secret_username = settings.PLUGINS_CONFIG['sidekick'].get('secret_user', None)
        private_key_path = settings.PLUGINS_CONFIG['sidekick'].get('secret_private_key_path', None)

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
                classes = snmpwalk_bulk_accounting(_mgmt_ip, snmp)
            except Exception as e:
                self.stdout.write(f"Error querying device {device}: {e}")
                return

            # Add any new classes to the database.
            for name, data in classes.items():
                try:
                    accounting_source = AccountingSource.objects.get(
                        device=device,
                        name=data['class'],
                    )
                except AccountingSource.DoesNotExist:
                    accounting_source = AccountingSource(
                        device=device,
                        name=data['class'],
                        destination=data['isp'],
                    )
                    if options['dry_run']:
                        self.stdout.write(f"Would have created AccountingSource {accounting_source}")
                    else:
                        accounting_source.save()
                except AccountingSource.MultipleObjectsReturned:
                    self.stdout.write(f"Multiple SCU/DCU classes found for {name} on {device}")

                # Add new counters to the databse.
                if options['dry_run']:
                    self.stdout.write(f"Would have updated counters for {accounting_source}")
                else:
                    counter = AccountingSourceCounter(
                        accounting_source=accounting_source,
                        scu=data['scu'],
                        dcu=data['dcu'],
                    )
                    counter.save()

                # Send the metrics to Graphite if graphite_host has been set.
                graphite_host = settings.PLUGINS_CONFIG['sidekick'].get('graphite_host', None)
                if graphite_host is not None:
                    graphyte.init(graphite_host)

                    # Determine the difference between the last two updates.
                    # This is because Cybera's metrics were previously stored in RRD
                    # files which only retains the derivative and not what the actual
                    # counters were.
                    previous_entries = AccountingSourceCounter.objects.filter(
                        accounting_source=accounting_source).order_by('-last_updated')
                    if len(previous_entries) < 2:
                        continue

                    e1 = previous_entries[0]
                    e2 = previous_entries[1]
                    total_seconds = (e1.last_updated - e2.last_updated).total_seconds()

                    graphite_prefix = "accounting.{}.{}".format(
                        e1.accounting_source.graphite_name(),
                        e1.accounting_source.graphite_destination_name())

                    for cat in ['scu', 'dcu']:
                        m1 = getattr(e1, cat, None)
                        m2 = getattr(e2, cat, None)
                        if m1 is not None and m2 is not None:
                            diff = (m1 - m2)

                            if diff != 0:
                                diff = diff / total_seconds
                            graphite_name = f"{graphite_prefix}.{cat}"
                            if options['dry_run']:
                                self.stdout.write(f"{graphite_name} {diff} {total_seconds}")
                            else:
                                graphyte.send(graphite_name, diff)
