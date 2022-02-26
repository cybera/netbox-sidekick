import csv

from django.core.management.base import BaseCommand
from django.utils.text import slugify

from dcim.models import Site
from tenancy.models import Tenant

from sidekick.utils import MEMBER_TYPES


class Command(BaseCommand):
    help = "Import existing members"

    def add_arguments(self, parser):
        parser.add_argument(
            '--file', required=True, help='The path to the CSV file')

        parser.add_argument(
            '--quiet', required=False, action='store_true',
            help='Suppress messages')

        parser.add_argument(
            '--dry-run', required=False, action='store_true',
            help='Perform a dry-run and make no changes')

    def handle(self, *args, **options):
        quiet = options['quiet']
        dry_run = options['dry_run']

        f = options['file']
        rows = []
        with open(f) as csvfile:
            r = csv.reader(csvfile)
            for row in r:
                rows.append(row)

        for row in rows:
            (name, description, member_type, comments, latitude, longitude) = row
            name = name.strip()

            if member_type not in MEMBER_TYPES:
                self.stdout.write(f"ERROR: Incorrect member type for {name}: {member_type}. Skipping.")
                continue

            # See if there is an existing tenant/member.
            # If there is, compare values and update as needed.
            # If there isn't, create one.
            try:
                changed = False
                tenant = Tenant.objects.get(name=name)

                if tenant.description != description:
                    changed = True
                    tenant.description = description
                    if dry_run or not quiet:
                        self.stdout.write(f"Changing description of {name} to {description}")

                if tenant.comments != comments:
                    changed = True
                    tenant.comments = comments
                    if dry_run or not quiet:
                        self.stdout.write(f"Changing comments of {name} to {comments}")

                if 'member_type' not in tenant.cf or tenant.cf['member_type'] != member_type:
                    changed = True
                    tenant.cf['member_type'] = member_type
                    if dry_run or not quiet:
                        self.stdout.write(f"Changing member_type of {name} to {member_type}")

                if not dry_run and changed:
                    self.stdout.write(f"Updated Tenant: {name}")
                    tenant.save()

            except Tenant.MultipleObjectsReturned:
                self.stdout.write(f"WARNING: Multiple results found for {name}. Skipping.")
                continue
            except Tenant.DoesNotExist:
                if options['dry_run']:
                    self.stdout.write(f"Would have created Tenant: {name}")
                    continue

                tenant = Tenant.objects.create(
                    name=name,
                    slug=slugify(name),
                    description=description,
                    comments=comments,
                )
                tenant.cf['member_type'] = member_type
                tenant.save()

                self.stdout.write(f"Created Tenant: {name}")

            # See if there is an existing site.
            # If there is, compare values and update as needed.
            # If there isn't, create one.
            try:
                changed = False
                site = Site.objects.get(name=name)

                if site.latitude != latitude:
                    changed = True
                    site.latitude = latitude
                    if dry_run or not quiet:
                        self.stdout.write(f"Changing latitude of Site {name} to {latitude}")

                if site.longitude != longitude:
                    changed = True
                    site.longitude = longitude
                    if dry_run or not quiet:
                        self.stdout.write(f"Changing longitude of Site {name} to {longitude}")

                if not dry_run and changed:
                    self.stdout.write(f"Updated Site: {name}")
                    site.save()

            except Site.MultipleObjectsReturned:
                self.stdout.write(f"WARNING: Multiple sites found for {name}. Skipping.")
                continue
            except Site.DoesNotExist:
                if options['dry_run']:
                    self.stdout.write(f"Would have created Site: {name}")
                    continue

                site = Site.objects.create(
                    name=name,
                    tenant=tenant,
                    slug=slugify(name),
                    latitude=latitude,
                    longitude=longitude,
                )
                site.save()

                self.stdout.write(f"Created Site: {name}")
