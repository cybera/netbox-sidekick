import csv

from django.core.management.base import BaseCommand
from django.utils.text import slugify

from tenancy.models import Tenant

from netbox_sidekick.models import Member, MemberType


class Command(BaseCommand):
    help = "Import existing member institutions"

    def add_arguments(self, parser):
        parser.add_argument(
            '--file', required=True, help='The path to the CSV file')

        parser.add_argument(
            '--dry-run', required=False, action='store_true',
            help='Perform a dry-run and make no changes')

    def handle(self, *args, **options):
        member = None

        f = options['file']
        rows = []
        with open(f) as csvfile:
            r = csv.reader(csvfile)
            for row in r:
                rows.append(row)

        for row in rows:
            (name, latitude, longitude, altitude, address, url, type) = row

            # Find the tenant with the same name.
            # If no match is found, raise an error and move on to the next.
            try:
                tenant = Tenant.objects.get(description=name)
            except Tenant.DoesNotExist:
                self.stdout.write(f"WARNING: No tenant found for {name}. Skipping.")
                continue

            # Find the matching member type.
            # If one doesn't exist, create it.
            try:
                member_type = MemberType.objects.get(name=type)
            except MemberType.MultipleObjectsReturned:
                self.stdout.write(f"WARNING: Multiple results found for {type}. Skipping.")
                continue
            except MemberType.DoesNotExist:
                if options['dry_run']:
                    self.stdout.write(f"Would have created Member Type: {type}")
                else:
                    member_type = MemberType.objects.create(name=type, slug=slugify(type))
                    self.stdout.write(f"Created Member Type: {type}")

            # Find the matching member.
            # If one doesn't exist, create one with basic information.
            try:
                member = Member.objects.get(tenant__description=name)

                # Update the member with latitude, longitude, and url.
                if options['dry_run']:
                    self.stdout.write(f"Would have updated {member}")
                else:
                    member.latitude = latitude
                    member.longitude = longitude
                    member.url = url
                    member.save()
                    self.stdout.write(f"Updated {member}")
            except Member.MultipleObjectsReturned:
                self.stdout.write(f"WARNING: Multiple results found for {name}. Skipping.")
                continue
            except Member.DoesNotExist:
                if options['dry_run']:
                    self.stdout.write(f"Would have created Member: {name}")
                else:
                    # Data from an institution spreadsheet doesn't have the
                    # same level of details as a member spreadsheet, so
                    # a lot of data is going to be blank and should be
                    # updated manually later.
                    member = Member.objects.create(
                        tenant=tenant,
                        member_type=member_type,
                        latitude=latitude,
                        longitude=longitude,
                        url=url,
                    )

                    self.stdout.write(f"Created Member: {member}")
