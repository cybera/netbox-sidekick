import csv

from django.core.management.base import BaseCommand
from django.utils.dateparse import parse_datetime
from django.utils.text import slugify

from tenancy.models import Tenant
from dcim.models import Site

from netbox_sidekick.models import (
    NetworkServiceType,
    NetworkService,
)


class Command(BaseCommand):
    help = "Import existing network services"

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
            (service_id, service_name, cust_id, service_type, l2_service_id, l3_service_id,
             notes, portal_statistics, service_archived, date_in_production, date_out_production,
             last_updated, service_status, group_id, group_type, group_name, group_desc,
             group_notes, group_archived, custom_client_id, custom_client_group_id,
             service_type_id, service_type_name, service_type_description, service_layer,
             service_type_archived) = row

            member_name = custom_client_id.strip().replace("&#039;", "'")

            # Find the matching service type.
            # If one doesn't exist, create one.
            try:
                service_type = NetworkServiceType.objects.get(name=service_type_name)
            except NetworkServiceType.MultipleObjectsReturned:
                self.stdout.write(
                    "WARNING: Multiple results found for " +
                    f"network service type {service_type}. Skipping.")
                continue
            except NetworkServiceType.DoesNotExist:
                service_type = NetworkServiceType(
                    name=service_type_name,
                    slug=slugify(service_type_name,))
                if dry_run:
                    self.stdout.write(
                        f"Would have created network service type: {service_type_name}")
                else:
                    service_type.save()
                    if not quiet:
                        self.stdout.write(f"Created network service type: {service_type_name}")

            # Find a matching member.
            # If one isn't found, skip.
            try:
                member = Tenant.objects.get(name=member_name)
            except Tenant.MultipleObjectsReturned:
                self.stdout.write(
                    f"WARNING: Multiple results found for Tenant {member_name}. Skipping.")
                continue
            except Tenant.DoesNotExist:
                self.stdout.write(f"WARNING: No member found for {member_name}. Skipping.")
                continue

            # Find a matching site.
            # If one isn't found, skip.
            try:
                member_site = Site.objects.get(name=member_name)
            except Tenant.MultipleObjectsReturned:
                self.stdout.write(
                    f"WARNING: Multiple results found for Site {member_name}. Skipping.")
                continue
            except Site.DoesNotExist:
                self.stdout.write(f"WARNING: No site found for {member_site}. Skipping.")
                continue

            # Find a matching service.
            # If one doesn't exist, create one.
            try:
                network_service = NetworkService.objects.get(
                    legacy_id=service_id,
                )
            except NetworkService.MultipleObjectsReturned:
                self.stdout.write(
                    "WARNING: Multiple results found for " +
                    f"network service {service_id}: {service_name}. Skipping.")
                continue
            except NetworkService.DoesNotExist:
                if date_in_production == 'NULL':
                    date_in_production = None
                elif date_in_production == '0000-00-00 00:00:00':
                    date_in_production = None
                else:
                    date_in_production = parse_datetime(date_in_production)

                if date_out_production == 'NULL':
                    date_out_production = None
                elif date_out_production == '0000-00-00 00:00:00':
                    date_out_production = None
                else:
                    date_out_production = parse_datetime(date_out_production)

                active = False
                if service_status == 'In Production' and int(service_archived) == 0:
                    active = True

                network_service = NetworkService(
                    name=service_name,
                    network_service_type=service_type,
                    member=member,
                    member_site=member_site,
                    comments=notes,
                    start_date=date_in_production,
                    end_date=date_out_production,
                    active=active,
                    legacy_id=service_id,
                )

                if dry_run:
                    self.stdout.write(
                        f"Would have created network service: {network_service}")
                else:
                    network_service.save()
                    if not quiet:
                        self.stdout.write(f"Created network service: {network_service}")
