import csv
import dateutil.parser as date_parser
import re

from django.core.management.base import BaseCommand
from django.utils.text import slugify

from tenancy.models import Tenant

from netbox_sidekick.models import (
    ContactType, Contact,
    MemberType, Member, MemberContact,
)

RE_YYYY_MM = re.compile(r'^\d\d\d\d-\d\d$')


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

        parser.add_argument(
            '--purge', required=False, action='store_true',
            help='Purge all data before importing')

    def handle(self, *args, **options):
        member = None
        member_type = None
        contact = None
        contact_type = None
        tenant = None

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

        if not options['dry_run'] and options['purge']:
            Member.objects.all().delete()
            MemberType.objects.all().delete()

        for row in rows:
            (name, type, start_date, invoice_period_start, users, connection,
             first_name, last_name, title, address_1,
             city, postal_code, phone, email, supernet) = row

            full_name = name.strip()
            short_name = name[:30].strip()

            # Find the matching member type.
            # If one doesn't exist, create one.
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

            # Find the tenant with the same name.
            # If no match is found, raise an error and halt.
            try:
                tenant = Tenant.objects.get(name=short_name)
            except Tenant.DoesNotExist:
                self.stdout.write(f"WARNING: No tenant found for {short_name}. Skipping.")
                continue

            # All contact types are assumed to be "billing".
            try:
                contact_type = ContactType.objects.get(name='Billing')
            except ContactType.DoesNotExist:
                if options['dry_run']:
                    self.stdout.write("Would have created Contact Type: Billing")
                else:
                    contact_type = ContactType.objects.create(name='Billing', slug='billing')
                    self.stdout.write("Created Contact Type: Billing")

            # Find a matching contact.
            # If no match is found, create one.
            try:
                contact = Contact.objects.get(
                    first_name=first_name,
                    last_name=last_name,
                    email=email,
                    phone=phone,
                )
            except Contact.MultipleObjectsReturned:
                self.stdout.write(f"WARNING: Multiple results found for {first_name} {last_name}. Skipping.")
                continue
            except Contact.DoesNotExist:
                if options['dry_run']:
                    self.stdout.write(f"Would have created Contact: {first_name} {last_name}")
                else:
                    contact = Contact.objects.create(
                        first_name=first_name,
                        last_name=last_name,
                        title=title,
                        email=email,
                        phone=phone,
                    )
                    self.stdout.write(f"Created Contact: {first_name} {last_name}")

            # Find a matching member.
            # If one isn't found, create one.
            try:
                member = Member.objects.get(tenant__name=short_name)
            except Member.MultipleObjectsReturned:
                self.stdout.write(f"WARNING: Multiple results found for {short_name}. Skipping.")
                continue
            except Member.DoesNotExist:
                if options['dry_run']:
                    self.stdout.write(f"Would have created Member: {short_name}")
                else:
                    # The date can be in a variety of formats.
                    # pre-2000
                    if 'pre-' in start_date:
                        start_date = start_date.replace('pre-', '')
                        start_date = f"{start_date}-01-01"

                    # 2000
                    if start_date.isnumeric():
                        start_date = f"{start_date}-01-01"

                    # 2000-01
                    if RE_YYYY_MM.match(start_date):
                        start_date = f"{start_date}-01"

                    try:
                        start_date = date_parser.parse(start_date)
                    except date_parser._parser.ParserError:
                        self.stdout.write(f"WARNING: Unable to parse date for {short_name}: {start_date}. Skipping.")

                    # supernet is stored as Y or N,
                    # so we convert to boolean
                    if supernet.lower() == 'y':
                        supernet = True
                    else:
                        supernet = False

                    member = Member.objects.create(
                        tenant=tenant,
                        member_type=member_type,
                        start_date=start_date,
                        invoice_period_start=invoice_period_start,
                        number_of_users=int(users.replace(',', '')),
                        billing_address_1=address_1,
                        billing_city=city,
                        billing_postal_code=postal_code,
                        billing_province='AB',
                        billing_country='Canada',
                        supernet=supernet,
                    )

                    self.stdout.write(f"Created Member: {member}")

            # Find a matching member contact.
            # If no match is found, create one.
            if contact is not None:
                try:
                    member_contact = MemberContact.objects.get(
                        contact=contact, member=member, type=contact_type)
                except MemberContact.MultipleObjectsReturned:
                    self.stdout.write(f"WARNING: Multiple results found for Member Contact {short_name} {first_name} {last_name}. Skipping.")
                    continue
                except MemberContact.DoesNotExist:
                    if options['dry_run']:
                        self.stdout.write(f"Would have created Member Contact: {short_name} {first_name} {last_name}")
                    else:
                        member_contact = MemberContact.objects.create(
                            contact=contact,
                            member=member,
                            type=contact_type,
                        )
                        self.stdout.write(f"Created Member Contact: {member_contact}")
