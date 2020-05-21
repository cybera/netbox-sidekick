import csv

from django.core.management.base import BaseCommand
from django.utils.text import slugify

from netbox_sidekick.models import (
    Member,
    MemberNode,
    MemberNodeLinkType, MemberNodeLink,
)


class Command(BaseCommand):
    help = "Import existing member node links"

    def add_arguments(self, parser):
        parser.add_argument(
            '--file', required=True, help='The path to the CSV file')

        parser.add_argument(
            '--dry-run', required=False, action='store_true',
            help='Perform a dry-run and make no changes')

        parser.add_argument(
            '--purge', required=False, action='store_true',
            help='Purge all data before importing')

    def handle(self, *args, **options):
        f = options['file']
        rows = []
        with open(f) as csvfile:
            r = csv.reader(csvfile)
            for row in r:
                rows.append(row)

        if not options['dry_run'] and options['purge']:
            MemberNodeLink.objects.all().delete()
            MemberNodeLinkType.objects.all().delete()

        for row in rows:
            (name, label, internal_id, a_endpoint, z_endpoint,
             type, throughput, owner, co_owner) = row

            # Find the matching node link type
            # If one doesn't exist, create one.
            try:
                type = MemberNodeLinkType.objects.get(name=type)
            except MemberNodeLinkType.MultipleObjectsReturned:
                self.stderr.write(f"WARNING: Multiple results found for {type}. Skipping.")
                continue
            except MemberNodeLinkType.DoesNotExist:
                if options['dry_run']:
                    self.stdout.write(f"Would have created Member Node Link Type: {type}")
                else:
                    type = MemberNodeLinkType.objects.create(name=type, slug=slugify(type))
                    self.stdout.write(f"Created Member Node Link Type: {type}")

            # Find the member who owns the node.
            # Default to "Cybera" if no owner was specified in the CSV.
            if owner == "":
                owner = "Cybera"

            try:
                member = Member.objects.get(tenant__description=owner)
            except Member.DoesNotExist:
                self.stdout.write(f"WARNING: No member found for {owner}. Skipping.")
                continue

            # Find the A Endpoint
            try:
                a_endpoint = MemberNode.objects.get(name=a_endpoint)
            except MemberNode.MultipleObjectsReturned:
                self.stderr.write(f"WARNING: Multiple results found for {a_endpoint}. Skipping.")
                continue
            except MemberNode.DoesNotExist:
                self.stderr.write(f"WARNING: No Member Node found for {a_endpoint}. Skipping.")
                continue

            # Find the Z Endpoint
            try:
                z_endpoint = MemberNode.objects.get(name=z_endpoint)
            except MemberNode.MultipleObjectsReturned:
                self.stderr.write(f"WARNING: Multiple results found for {z_endpoint}. Skipping.")
                continue
            except MemberNode.DoesNotExist:
                self.stderr.write(f"WARNING: No Member Node found for {z_endpoint}. Skipping.")
                continue

            # Find the link
            try:
                MemberNodeLink.objects.get(name=name)
            except MemberNodeLink.MultipleObjectsReturned:
                self.stdout.write(f"WARNING: Multiple results found for {name}. Skipping.")
            except MemberNodeLink.DoesNotExist:
                if options['dry_run']:
                    self.stdout.write(f"Would have created Member Node Link: {name}")
                else:
                    if throughput == "":
                        throughput = 0

                    link = MemberNodeLink.objects.create(
                        name=name,
                        label=label,
                        internal_id=internal_id,
                        a_endpoint=a_endpoint,
                        z_endpoint=z_endpoint,
                        link_type=type,
                        throughput=throughput,
                        owner=member,
                    )

                    self.stdout.write(f"Created Member Node Link: {link}")
