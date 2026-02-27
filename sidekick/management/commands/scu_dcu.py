import graphyte
import os

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
    decrypt_1pw_secret,
    snmpwalk_bulk_accounting,
)
from sidekick.utils.clickhouse import ClickHouseHTTP, now_utc_str


scudcu_map = {
    'scu': 'in_octets',
    'dcu': 'out_octets',
}


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
        onepw_host = settings.PLUGINS_CONFIG['sidekick'].get('1pw_connect_host', None)
        onepw_token_path = settings.PLUGINS_CONFIG['sidekick'].get('1pw_connect_token_path', None)
        onepw_vault = settings.PLUGINS_CONFIG['sidekick'].get('1pw_connect_readonly_vault', None)

        # If all of the connection information was found,
        # attempt to decrypt the connection credentials,
        # connect to the device, and inventory the interfaces.
        if mgmt_ip is not None and \
           onepw_host is not None and \
           onepw_token_path is not None and \
           onepw_vault is not None:

            _mgmt_ip = "%s" % (mgmt_ip.address.ip)

            try:
                snmp = decrypt_1pw_secret(onepw_token_path, onepw_host, onepw_vault, f"{device.name}", 'snmp')

            except Exception as e:
                self.stdout.write(f"Unable to decrypt snmp secret: {e}")

            if snmp is None:
                self.stdout.write(f"Unable to find snmp secret for {device}")
                return

            ch = None
            ch_url = settings.PLUGINS_CONFIG['sidekick'].get('clickhouse_url', None)
            if not ch_url:
                ch_url = os.getenv("CLICKHOUSE_URL")
            ch_user = settings.PLUGINS_CONFIG['sidekick'].get('clickhouse_user', None)
            if not ch_user:
                ch_user = os.getenv("CLICKHOUSE_USER", "")
            ch_password = settings.PLUGINS_CONFIG['sidekick'].get('clickhouse_password', None)
            if not ch_password:
                ch_password = os.getenv("CLICKHOUSE_PASSWORD", "")
            ch_db = settings.PLUGINS_CONFIG['sidekick'].get('clickhouse_database', None)
            if not ch_db:
                ch_db = os.getenv("CLICKHOUSE_DATABASE") or os.getenv("CLICKHOUSE_NETFLOW_DATABASE") or "pmacct"
            ch_table = settings.PLUGINS_CONFIG['sidekick'].get('clickhouse_legacy_table', None)
            if not ch_table:
                ch_table = os.getenv("CLICKHOUSE_LEGACY_TABLE", "nic_deltas_5m")

            if ch_url and ch_db:
                try:
                    ch = ClickHouseHTTP(base_url=ch_url, user=ch_user, password=ch_password, database=ch_db)
                except Exception as e:
                    self.stdout.write(f"WARNING: ClickHouse init failed: {e}")

            try:
                classes = snmpwalk_bulk_accounting(_mgmt_ip, snmp)
            except Exception as e:
                self.stdout.write(f"Error querying device {device}: {e}")
                return

            # Add any new classes to the database.
            ch_rows = []
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
                results = None
                if options['dry_run']:
                    self.stdout.write(f"Would have updated counters for {accounting_source}")
                else:
                    counter = AccountingSourceCounter(
                        accounting_source=accounting_source,
                        scu=data['scu'],
                        dcu=data['dcu'],
                    )
                    counter.save()
                    results = accounting_source.get_current_rate()

                # Collect ClickHouse rows
                if ch is not None and results:
                    for cat in ['scu', 'dcu']:
                        ch_rows.append({
                            "ts": now_utc_str(),
                            "interface_id": None,
                            "accounting_source_id": accounting_source.id,
                            "metric": cat,
                            "delta": float(results[cat]),
                        })

                # Send the metrics to Graphite if graphite_host has been set.
                graphite_host = settings.PLUGINS_CONFIG['sidekick'].get('graphite_host', None)
                if graphite_host is not None:
                    graphyte.init(graphite_host)

                    # Determine the difference between the last two updates.
                    # This is because Cybera's metrics were previously stored in RRD
                    # files which only retains the derivative and not what the actual
                    # counters were.
                    if results is None:
                        results = accounting_source.get_current_rate()

                    graphite_prefix = "accounting.{}.{}".format(
                        accounting_source.graphite_name(),
                        accounting_source.graphite_destination_name())

                    for cat in ['scu', 'dcu']:
                        graphite_name = f"{graphite_prefix}.{scudcu_map[cat]}"
                        if options['dry_run']:
                            self.stdout.write(f"{graphite_name} {results[cat]}")
                        else:
                            graphyte.send(graphite_name, results[cat])

            if ch is not None and ch_rows:
                try:
                    ch.insert_json_each_row(f"{ch_db}.{ch_table}", ch_rows)
                except Exception as e:
                    self.stdout.write(f"WARNING: ClickHouse insert failed: {e}")
