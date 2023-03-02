import re

from django.http import Http404

from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.renderers import JSONRenderer
from rest_framework.views import APIView

from netbox.api.authentication import TokenAuthentication
from netbox.api.viewsets import NetBoxModelViewSet

from sidekick.api.serializers import (
    AccountingProfileSerializer,
    AccountingSourceSerializer,
    BandwidthProfileSerializer,
)

from sidekick.filters import (
    AccountingProfileFilterSet
)

from sidekick.models import (
    AccountingProfile,
    AccountingSource,
    BandwidthProfile,
)


class AccountingProfileViewSet(NetBoxModelViewSet):
    queryset = AccountingProfile.objects.all()
    serializer_class = AccountingProfileSerializer
    filterset_class = AccountingProfileFilterSet


class AccountingSourceViewSet(NetBoxModelViewSet):
    queryset = AccountingSource.objects.all()
    serializer_class = AccountingSourceSerializer


class BandwidthProfileViewSet(NetBoxModelViewSet):
    queryset = BandwidthProfile.objects.all()
    serializer_class = BandwidthProfileSerializer


class CurrentBandwidthView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    renderer_class = JSONRenderer

    def get(self, request, profile=None):
        profile_id = self.kwargs.get('profile', None)
        if profile_id is None:
            raise Http404

        # Ensure the profile exists.
        try:
            ap = AccountingProfile.objects.get(id=profile_id)
        except AccountingProfile.DoesNotExist:
            raise Http404

        result = {}
        bp = ap.get_current_bandwidth_profile()
        if bp is not None:
            traffic_cap = bp.traffic_cap
            result["member_name"] = ap.member.name
            result['traffic_cap'] = traffic_cap

            result['accounting_sources'] = {}
            for accounting_source in ap.accounting_sources.all():
                result['accounting_sources'][f"{accounting_source}"] = {}
                result['accounting_sources'][f"{accounting_source}"]["name"] = accounting_source.name
                result['accounting_sources'][f"{accounting_source}"]["destination"] = accounting_source.destination

                current_rate = accounting_source.get_current_rate()
                result['accounting_sources'][f"{accounting_source}"]["current_rate"] = current_rate

        return Response(result)


class AllCurrentBandwidthView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    renderer_class = JSONRenderer

    def get(self, request):
        results = []
        for accounting_profile in AccountingProfile.objects.filter(enabled=True):
            bandwidth_profile = accounting_profile.get_current_bandwidth_profile()
            if bandwidth_profile is not None:
                v = {}
                v['member_name'] = accounting_profile.member.name
                v['member_name_slug'] = re.sub(r'[ -./\'\(\)]+', '', accounting_profile.member.name)
                v['traffic_cap'] = bandwidth_profile.traffic_cap
                v['burst_limit'] = bandwidth_profile.burst_limit
                v['accounting_sources'] = []
                for accounting_source in accounting_profile.accounting_sources.all():
                    t = {}
                    t['device'] = accounting_source.device.name
                    t['name'] = accounting_source.name
                    t['destination'] = accounting_source.destination
                    v['accounting_sources'].append(t)

                results.append(v)

        return Response(results)
