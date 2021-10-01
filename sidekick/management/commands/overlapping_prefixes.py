import netaddr

from django.core.management.base import BaseCommand

from sidekick.models import NetworkService


class Command(BaseCommand):
    help = "Checks for members with overlapping IP prefixes/subnets"

    def handle(self, *args, **options):
        v4_prefixes = {}
        v6_prefixes = {}

        for ns in NetworkService.objects.filter(active=True):
            member_name = ns.member.name
            if member_name not in v4_prefixes:
                v4_prefixes[member_name] = []
            if member_name not in v6_prefixes:
                v6_prefixes[member_name] = []

            v4_prefixes[member_name].extend(ns.get_ipv4_prefixes())
            v6_prefixes[member_name].extend(ns.get_ipv6_prefixes())

        for i_member, i_prefixes in v4_prefixes.items():
            for j_member, j_prefixes in v4_prefixes.items():
                if i_member == j_member:
                    continue

                j = netaddr.IPSet(j_prefixes)
                for prefix in i_prefixes:
                    if prefix in j:
                        self.stdout.write(f"Overlap: {i_member} and {j_member}: {prefix}")

        for i_member, i_prefixes in v6_prefixes.items():
            for j_member, j_prefixes in v6_prefixes.items():
                if i_member == j_member:
                    continue

                j = netaddr.IPSet(j_prefixes)
                for prefix in i_prefixes:
                    if prefix in j:
                        self.stdout.write(f"Overlap: {i_member} and {j_member}: {prefix}")
