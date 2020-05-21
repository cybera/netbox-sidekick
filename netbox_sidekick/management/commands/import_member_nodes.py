import csv

from django.core.management.base import BaseCommand
from django.utils.text import slugify

from netbox_sidekick.models import MemberNodeType, MemberNode, Member


class Command(BaseCommand):
    help = "Import existing member nodes"

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
            MemberNode.objects.all().delete()
            MemberNodeType.objects.all().delete()

        for row in rows:
            (name, label, internal_id, latitude, longitude,
             altitude, address, type, owner, co_owner) = row

            # Find the matching node type
            # If one doesn't exist, create one.
            try:
                type = MemberNodeType.objects.get(name=type)
            except MemberNodeType.MultipleObjectsReturned:
                self.stderr.write(f"WARNING: Multiple results found for {type}. Skipping.")
                continue
            except MemberNodeType.DoesNotExist:
                if options['dry_run']:
                    self.stdout.write(f"Would have created Member Node Type: {type}")
                else:
                    type = MemberNodeType.objects.create(name=type, slug=slugify(type))
                    self.stdout.write(f"Created Member Node Type: {type}")

            # Find the member who owns the node.
            # Default to "Cybera" if no owner was specified in the CSV.
            if owner == "":
                owner = "Cybera"

            try:
                member = Member.objects.get(tenant__description=owner)
            except Member.DoesNotExist:
                self.stdout.write(f"WARNING: No member found for {owner}. Skipping.")
                continue

            # Find a matching node name.
            # If one doesn't exist, create one.
            try:
                MemberNode.objects.get(name=name)
            except MemberNode.MultipleObjectsReturned:
                self.stdout.write(f"WARNING: Multiple results found for {name}. Skipping.")
                continue
            except MemberNode.DoesNotExist:
                if options['dry_run']:
                    self.stdout.write(f"Would have created Member Node: {name}")
                else:
                    member_node = MemberNode.objects.create(
                        name=name,
                        node_type=type,
                        label=label,
                        internal_id=internal_id,
                        latitude=latitude,
                        longitude=longitude,
                        owner=member,
                    )

                    self.stdout.write(f"Created Member Node: {member_node}")
