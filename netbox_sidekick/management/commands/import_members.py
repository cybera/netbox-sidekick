import csv
import dateutil.parser as date_parser

from django.core.management.base import BaseCommand
from django.utils.text import slugify

from tenancy.models import Tenant

from netbox_sidekick.models import MemberType, Member


class Command(BaseCommand):
    help = "Import existing members"

    def add_arguments(self, parser):
        parser.add_argument(
            '--file', required=True, help='The path to the CSV file')

        parser.add_argument(
            '--reconcile', required=False, action='store_true',
            help='Determine missing members or tenants')

        parser.add_argument(
            '--dry-run', required=False, action='store_true',
            help='Perform a dry-run and make no changes')

    def handle(self, *args, **options):
        f = options['file']
        rows = []
        with open(f) as csvfile:
            r = csv.reader(csvfile)
            for row in r:
                rows.append(row)

        if options['reconcile']:
            members = {}
            tenants = {}
            for t in Tenant.objects.filter(group__name="Members"):
                tenants[t.name] = t.description

            for row in rows:
                full_name = row[0].strip()
                # NetBox limits tenant names to 30 characters.
                # The full name is stored as the tenant's description.
                short_name = row[0][:30].strip()
                members[full_name] = short_name

            for full_name, short_name in members.items():
                if short_name not in tenants:
                    self.stdout.write("Tenant not found: %s" % (short_name))

                if full_name not in tenants.values():
                    self.stdout.write("Tenant not found: %s" % (full_name))

            for tname, tdesc in tenants.items():
                if tname not in members.values():
                    self.stdout.write("Member not found: %s" % (tname))

            return

        for row in rows:
            (name, type, start_date, invoice_period_start, users, connection,
             billing_first_name, billing_last_name, billing_title, address_1,
             city, postal_code, phone, email, supernet) = row

            full_name = name.strip()
            short_name = name[:30].strip()

            # Find the matching member type.
            # If one doesn't exist, create one.
            try:
                type = MemberType.objects.get(name=type)
            except MemberType.MultipleObjectsReturned:
                self.stdout.write(f"WARNING: Multiple results found for {type}. Skipping.")
                continue
            except MemberType.DoesNotExist:
                if options['dry_run']:
                    self.stdout.write(f"Would have created Member Type: {type}")
                else:
                    type = MemberType.objects.create(name=type, slug=slugify(type))
                    self.stdout.write(f"Created Member Type: {type}")

            # Find the tenant with the same name.
            # If no match is found, raise an error and halt.
            try:
                tenant = Tenant.objects.get(name=short_name)
            except Tenant.DoesNotExist:
                self.stdout.write(f"WARNING: No tenant found for {short_name}. Skipping.")
                continue

            # Find a matching member.
            # If one isn't found, record it for creation.
            try:
                Member.objects.get(tenant__name=short_name)
            except Member.MultipleObjectsReturned:
                self.stdout.write(f"WARNING: Multiple results found for {short_name}. Skipping.")
                continue
            except Member.DoesNotExist:
                if options['dry_run']:
                    self.stdout.write(f"Would have created Member: {short_name}")
                else:
                    # The date is recorded as 2020-05,
                    # so we add -01 at the end to make 2020-05-01.
                    start_date = "%s-01" % (start_date)
                    start_date = date_parser.parse(start_date)

                    # supernet is stored as Y or N,
                    # so we convert to boolean
                    if supernet.lower() == 'y':
                        supernet = True
                    else:
                        supernet = False

                    member = Member.objects.create(
                        tenant=tenant,
                        member_type=type,
                        start_date=start_date,
                        invoice_period_start=invoice_period_start,
                        number_of_users=users,
                        billing_contact_first_name=billing_first_name,
                        billing_contact_last_name=billing_last_name,
                        billing_contact_title=billing_title,
                        billing_contact_phone_number=phone,
                        billing_contact_email_address=email,
                        billing_address_1=address_1,
                        billing_city=city,
                        billing_postal_code=postal_code,
                        billing_province='AB',
                        billing_country='Canada',
                        supernet=supernet,
                    )

                    self.stdout.write(f"Created Member: {member}")
