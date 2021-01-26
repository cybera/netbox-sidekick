import csv

from django.core.management.base import BaseCommand
from django.utils.text import slugify

from netbox_sidekick.models import (
    LogicalSystem,
    NetworkServiceDevice,
    NetworkServiceL3,
    RoutingType,
)


class Command(BaseCommand):
    help = "Import existing network service L3 details"

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

        clean_addresses = [
            'address ',
            'NULL',
        ]

        f = options['file']
        rows = []
        with open(f) as csvfile:
            r = csv.reader(csvfile, delimiter='\t')
            for row in r:
                rows.append(row)

        for row in rows:
            (service_id, l3_service_id, name, cust_id, routing_type_name, service_type,
             logical_system_name, ipv4_unicast, ipv4_multicast, ipv6_unicast,
             ipv6_multicast, ipv4_prefixes, ipv6_prefixes,
             provider_ipv4, member_ipv4, provider_ipv6, member_ipv6,
             mtu, bgp_as, bgp_pass, traffic_policing, device_id, notes) = row

            for i in clean_addresses:
                provider_ipv4 = provider_ipv4.replace(i, '')
                member_ipv4 = member_ipv4.replace(i, '')
                provider_ipv6 = provider_ipv6.replace(i, '')
                member_ipv6 = member_ipv6.replace(i, '')

            ipv4_prefixes = ipv4_prefixes.replace('\\n', '\n')
            ipv6_prefixes = ipv6_prefixes.replace('\\n', '\n')

            ipv4_unicast = bool(ipv4_unicast)
            ipv4_multicast = bool(ipv4_multicast)
            ipv6_unicast = bool(ipv6_unicast)
            ipv6_multicast = bool(ipv6_multicast)

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

            # Find a matching routing type.
            # If one isn't found, create one.
            try:
                routing_type = RoutingType.objects.get(
                    name=routing_type_name,
                )
            except RoutingType.MultipleObjectsReturned:
                self.stdout.write(f"WARNING: Multiple results found for Routing Type {routing_type_name}. Skipping.")
                continue
            except RoutingType.DoesNotExist:
                routing_type = RoutingType(
                    name=routing_type_name,
                    slug=slugify(routing_type_name),
                )

                if dry_run:
                    self.stdout.write(f"Would have created routing type: {routing_type}")
                else:
                    routing_type.save()
                    if not quiet:
                        self.stdout.write(f"Created routing type: {routing_type}")

            # Find a matching logical system.
            # If one isn't found, create one.
            try:
                logical_system = LogicalSystem.objects.get(
                    slug=slugify(logical_system_name),
                )
            except LogicalSystem.MultipleObjectsReturned:
                self.stdout.write(
                    "WARNING: Multiple results found for " +
                    f"Logical Router {logical_system_name}. Skipping.")
                continue
            except LogicalSystem.DoesNotExist:
                logical_system = LogicalSystem(
                    name=logical_system_name,
                    slug=slugify(logical_system_name),
                )

                if dry_run:
                    self.stdout.write(f"Would have created logical system: {logical_system}")
                else:
                    logical_system.save()
                    if not quiet:
                        self.stdout.write(f"Created logical system: {logical_system}")

            # Find a matching L3 service.
            # If one isn't found, create one.
            try:
                l3_service = NetworkServiceL3.objects.get(
                    legacy_id=l3_service_id,
                )

                changed = []
                if l3_service.routing_type != routing_type:
                    changed.append(f"{l3_service.routing_type} => {routing_type}")
                    l3_service.routing_type = routing_type

                if l3_service.logical_system != logical_system:
                    changed.append(f"{l3_service.logical_system} => {logical_system}")
                    l3_service.logical_system = logical_system

                if l3_service.ipv4_unicast != ipv4_unicast:
                    changed.append(f"{l3_service.ipv4_unicast} => {ipv4_unicast}")
                    l3_service.ipv4_unicast = ipv4_unicast

                if l3_service.ipv4_multicast != ipv4_multicast:
                    changed.append(f"{l3_service.ipv4_multicast} => {ipv4_multicast}")
                    l3_service.ipv4_multicast = ipv4_multicast

                if l3_service.ipv4_prefixes != ipv4_prefixes:
                    changed.append(f"{l3_service.ipv4_prefixes} => {ipv4_prefixes}")
                    l3_service.ipv4_prefixes = ipv4_prefixes

                if l3_service.provider_router_address_ipv4 != provider_ipv4:
                    changed.append(
                        f"{l3_service.provider_router_address_ipv4} => {provider_ipv4}")
                    l3_service.provider_router_address_ipv4 = provider_ipv4

                if l3_service.member_router_address_ipv4 != member_ipv4:
                    changed.append(
                        f"{l3_service.member_router_address_ipv4} => {member_ipv4}")
                    l3_service.member_router_address_ipv4 = member_ipv4

                if l3_service.provider_router_address_ipv6 != provider_ipv6:
                    changed.append(
                        f"{l3_service.provider_router_address_ipv6} => {provider_ipv6}")
                    l3_service.provider_router_address_ipv6 = provider_ipv6

                if l3_service.member_router_address_ipv6 != member_ipv6:
                    changed.append(
                        f"{l3_service.member_router_address_ipv6} => {member_ipv6}")
                    l3_service.member_router_address_ipv6 = member_ipv6

                if l3_service.ipv6_unicast != ipv6_unicast:
                    changed.append(f"{l3_service.ipv6_unicast} => {ipv6_unicast}")
                    l3_service.ipv6_unicast = ipv6_unicast

                if l3_service.ipv6_multicast != ipv6_multicast:
                    changed.append(f"{l3_service.ipv6_multicast} => {ipv6_multicast}")
                    l3_service.ipv6_multicast = ipv6_multicast

                if l3_service.ipv6_prefixes != ipv6_prefixes:
                    changed.append(f"{l3_service.ipv6_prefixes} => {ipv6_prefixes}")
                    l3_service.ipv6_prefixes = ipv6_prefixes

                if l3_service.asn != bgp_as:
                    changed.append(f"{l3_service.asn} => {bgp_as}")
                    l3_service.asn = bgp_as

                if len(changed) > 0:
                    if dry_run:
                        self.stdout.write(f"Would have updated {l3_service}: {changed}")
                    else:
                        l3_service.save()
                        if not quiet:
                            self.stdout.write(f"Updated {l3_service}: {changed}")

            except NetworkServiceL3.DoesNotExist:
                l3_service = NetworkServiceL3(
                    network_service_device=network_service_device,
                    legacy_id=l3_service_id,
                    routing_type=routing_type,
                    logical_system=logical_system,
                    ipv4_unicast=ipv4_unicast,
                    ipv4_multicast=ipv4_multicast,
                    ipv4_prefixes=ipv4_prefixes,
                    provider_router_address_ipv4=provider_ipv4,
                    member_router_address_ipv4=member_ipv4,
                    provider_router_address_ipv6=provider_ipv6,
                    member_router_address_ipv6=member_ipv6,
                    ipv6_unicast=ipv6_unicast,
                    ipv6_multicast=ipv6_multicast,
                    ipv6_prefixes=ipv6_prefixes,
                    asn=bgp_as,
                )

                if dry_run:
                    self.stdout.write(f"Would have created {l3_service}")
                else:
                    l3_service.save()
                    if not quiet:
                        self.stdout.write(f"Created {l3_service}")
