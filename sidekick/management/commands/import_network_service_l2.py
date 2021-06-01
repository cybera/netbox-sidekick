import csv

from django.core.management.base import BaseCommand

from sidekick.models import (
    NetworkServiceDevice,
    NetworkServiceL2,
)


class Command(BaseCommand):
    help = "Import existing network service L2 details"

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
            (service_id, l2_service_id, vlan, notes) = row

            # Find a matching service device.
            # If one isn't found, skip.
            try:
                network_service_device = NetworkServiceDevice.objects.get(
                    network_service__legacy_id=service_id,
                )
            except NetworkServiceDevice.MultipleObjectsReturned:
                self.stdout.write(f"WARNING: Multiple results found for Service {service_id}. Skipping.")
                continue
            except NetworkServiceDevice.DoesNotExist:
                self.stdout.write(f"WARNING: No service found for {service_id}. Skipping.")
                continue

            # Find a matching L2 service.
            # If one isn't found, create one.
            try:
                l2_service = NetworkServiceL2.objects.get(
                    legacy_id=l2_service_id,
                )

                changed = []
                if l2_service.vlan != vlan:
                    changed.append(f"{l2_service.vlan} => {vlan}")
                    l2_service.vlan = vlan

                if l2_service.comments != notes:
                    changed.append(f"{l2_service.comments} => {notes}")
                    l2_service.comments = notes

                if len(changed) > 0:
                    if dry_run:
                        self.stdout.write(f"Would have updated {l2_service}: {changed}")
                    else:
                        l2_service.save()
                        if not quiet:
                            self.stdout.write(f"Updated {l2_service}: {changed}")

            except NetworkServiceL2.DoesNotExist:
                l2_service = NetworkServiceL2(
                    network_service_device=network_service_device,
                    vlan=vlan,
                    comments=notes,
                    legacy_id=l2_service_id,
                )

                if dry_run:
                    self.stdout.write(f"Would have created {l2_service}")
                else:
                    l2_service.save()
                    if not quiet:
                        self.stdout.write(f"Created {l2_service}")
