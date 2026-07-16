from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.renderers import JSONRenderer
from rest_framework.views import APIView

from netbox.api.authentication import TokenAuthentication
from netbox.api.viewsets import NetBoxModelViewSet

from sidekick.api.renderers.plaintext import PlainTextRenderer

from sidekick.api.serializers import (
    LogicalSystemSerializer,
    RoutingTypeSerializer,
    NetworkServiceTypeSerializer,
    NetworkServiceSerializer,
    NetworkServiceDeviceSerializer,
    NetworkServiceL2Serializer,
    NetworkServiceL3Serializer,
    NetworkServiceGroupSerializer,
)

from sidekick.models import (
    LogicalSystem,
    RoutingType,
    NetworkServiceType,
    NetworkService,
    NetworkServiceDevice,
    NetworkServiceL2,
    NetworkServiceL3,
    NetworkServiceGroup,
)


class LogicalSystemViewSet(NetBoxModelViewSet):
    queryset = LogicalSystem.objects.all()
    serializer_class = LogicalSystemSerializer


class RoutingTypeViewSet(NetBoxModelViewSet):
    queryset = RoutingType.objects.all()
    serializer_class = RoutingTypeSerializer


class NetworkServiceTypeViewSet(NetBoxModelViewSet):
    queryset = NetworkServiceType.objects.all()
    serializer_class = NetworkServiceTypeSerializer


class NetworkServiceViewSet(NetBoxModelViewSet):
    queryset = NetworkService.objects.all()
    serializer_class = NetworkServiceSerializer


class NetworkServiceDeviceViewSet(NetBoxModelViewSet):
    queryset = NetworkServiceDevice.objects.all()
    serializer_class = NetworkServiceDeviceSerializer


class NetworkServiceL2ViewSet(NetBoxModelViewSet):
    queryset = NetworkServiceL2.objects.all()
    serializer_class = NetworkServiceL2Serializer


class NetworkServiceL3ViewSet(NetBoxModelViewSet):
    queryset = NetworkServiceL3.objects.all()
    serializer_class = NetworkServiceL3Serializer


class NetworkServiceGroupViewSet(NetBoxModelViewSet):
    queryset = NetworkServiceGroup.objects.all()
    serializer_class = NetworkServiceGroupSerializer


class NetworkServiceDuplicateInterfaces(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    renderer_class = JSONRenderer

    def get(self, request):
        service_devices = NetworkServiceDevice.objects.filter(network_service__active=True)
        interfaces = {}
        for sd in service_devices:
            dev_name = sd.device.name
            if dev_name not in interfaces:
                interfaces[dev_name] = {}
            if sd.interface not in interfaces[dev_name]:
                interfaces[dev_name][sd.interface] = 1
            else:
                interfaces[dev_name][sd.interface] += 1

        result = []
        for dev, i in interfaces.items():
            duplicates = [k for k, v in i.items() if v > 1]
            if len(duplicates) > 0:
                result.append(f"Multiple services using {duplicates} on {dev}")

        return Response(result)


class NetworkServiceAdvertisedPrefixes(APIView):
    """Returns advertised prefixes as plain text (one CIDR per line).

    Query params:
        service_type: repeatable, defaults to ['transit', 'c-all']
        version: 4 (default) or 6
    """
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    renderer_classes = (PlainTextRenderer,)

    def get(self, request):
        service_type = request.query_params.getlist('service_type', ['transit', 'c-all'])
        if not isinstance(service_type, list):
            service_type = [service_type]

        version = request.query_params.get('version', 4)
        try:
            version = int(version)
        except ValueError:
            version = 4

        prefixes = []
        for network_service in NetworkService.objects.filter(active=True).filter(network_service_type__name__in=service_type):
            for prefix in network_service.get_prefixes(version=version):
                p = "%s" % (prefix)
                if p not in prefixes:
                    prefixes.append(p)

        return Response("\n".join(prefixes))


class NetworkServiceFastNetMonData(APIView):
    """Returns a consolidated JSON payload for FastNetMon configuration.

    This endpoint serves two purposes in a single call:

    1. **all_prefixes**: A flat, sorted, deduplicated list of all advertised
       prefixes from active transit/c-all network services. This is the source
       of truth for FastNetMon's `networks_list` (Phase 2: replaces the manual
       `fcli set main networks_list` procedure documented in the FNM SOP).

    2. **members**: A per-member breakdown with transit cap and prefixes, for
       building per-member FastNetMon hostgroups with thresholds derived from
       contracted rates (Phase 3: `threshold_mbps = traffic_cap * multiplier`).

    Query params:
        service_type: repeatable, defaults to ['transit', 'c-all']
        include_traffic_cap: if true (default), resolve the current
            BandwidthProfile.traffic_cap for each member via the
            NetworkService.accounting_profile relationship.

    Response shape::

        {
          "all_prefixes": ["199.216.82.0/24", ...],
          "members": [
            {
              "member_name": "Some Member",
              "member_slug": "somemember",
              "traffic_cap_mbps": 1000,
              "has_traffic_cap": true,
              "prefixes": ["199.216.82.0/24", ...]
            },
            ...
          ]
        }
    """
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    renderer_classes = (JSONRenderer,)

    def get(self, request):
        import re

        service_type = request.query_params.getlist('service_type', ['transit', 'c-all'])
        if not isinstance(service_type, list):
            service_type = [service_type]

        version = request.query_params.get('version', 4)
        try:
            version = int(version)
        except ValueError:
            version = 4

        all_prefixes = set()
        members = {}

        services = NetworkService.objects.filter(
            active=True,
            network_service_type__name__in=service_type,
        ).select_related(
            'member',
            'accounting_profile',
        )

        for ns in services:
            # Resolve prefixes for this service.
            ns_prefixes = []
            for prefix in ns.get_prefixes(version=version):
                p = str(prefix)
                ns_prefixes.append(p)
                all_prefixes.add(p)

            # Resolve the member. NetworkServiceL3 may override the member for
            # peering connections, but at the NetworkService level the member
            # is the service owner.
            if ns.member is None:
                continue

            member_name = ns.member.name
            member_slug = re.sub(r'[^a-zA-Z0-9]', '', member_name).lower()

            if member_slug not in members:
                # Resolve the traffic cap from the accounting profile's current
                # bandwidth profile (most recent effective_date <= now).
                traffic_cap = None
                if ns.accounting_profile is not None:
                    bp = ns.accounting_profile.get_current_bandwidth_profile()
                    if bp is not None and bp.traffic_cap is not None:
                        traffic_cap = bp.traffic_cap

                members[member_slug] = {
                    'member_name': member_name,
                    'member_slug': member_slug,
                    'traffic_cap_mbps': traffic_cap,
                    'has_traffic_cap': traffic_cap is not None,
                    'prefixes': set(),
                }

            members[member_slug]['prefixes'].update(ns_prefixes)

        # Build the response: convert sets to sorted lists.
        members_list = []
        for slug, data in sorted(members.items()):
            members_list.append({
                'member_name': data['member_name'],
                'member_slug': slug,
                'traffic_cap_mbps': data['traffic_cap_mbps'],
                'has_traffic_cap': data['has_traffic_cap'],
                'prefixes': sorted(data['prefixes']),
            })

        return Response({
            'all_prefixes': sorted(all_prefixes),
            'members': members_list,
        })
