import re

from django.db.models import Prefetch
from django.http import Http404
from django.utils import timezone

from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.renderers import JSONRenderer
from rest_framework.views import APIView

from netbox.api.authentication import TokenAuthentication
from netbox.api.viewsets import NetBoxModelViewSet

from tenancy.models import ContactAssignment

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
    AccountingSourceCounter,
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

    @staticmethod
    def _current_rate(accounting_source):
        """Same computation as AccountingSource.get_current_rate(), but
        using the prefetched `recent` counters (ordered by -last_updated)
        so that all sources' rates can be computed in bulk."""
        results = {
            'scu': 0,
            'dcu': 0,
        }

        entries = accounting_source.recent
        if len(entries) < 2:
            return results

        e1, e2 = entries[0], entries[1]
        total_seconds = (e1.last_updated - e2.last_updated).total_seconds()
        if total_seconds == 0:
            # Two entries sharing a timestamp would divide by zero;
            # treat the rate as 0 (no usage detected).
            return results

        for cat in ('scu', 'dcu'):
            m1 = getattr(e1, cat, None)
            m2 = getattr(e2, cat, None)
            if m1 is not None and m2 is not None:
                diff = (m1 - m2)
                if diff != 0:
                    diff = diff / total_seconds
                    results[cat] = diff

        return results

    def get(self, request):
        results = []
        now = timezone.now()

        # Prefetch everything the response needs in a fixed number of
        # queries. AccountingSourceCounter.save() keeps at most 5 rows per
        # source, so fetching all counters per source is cheap and lets
        # every source's current rate be computed in bulk. This replaces
        # the previous per-profile query pattern (bandwidth profile,
        # sites, contacts, sources and rates were one or more queries
        # per profile, i.e. 90+ queries per request).
        counters_qs = AccountingSourceCounter.objects.order_by('-last_updated')
        accounting_profiles = (
            AccountingProfile.objects
            .filter(enabled=True)
            .select_related('member')
            .prefetch_related(
                'bandwidthprofile_set',
                'member__sites',
                Prefetch('member__sites__contacts',
                         queryset=ContactAssignment.objects
                         .select_related('contact', 'role')),
                Prefetch('accounting_sources',
                         queryset=AccountingSource.objects
                         .select_related('device')
                         .prefetch_related(Prefetch('accountingsourcecounter_set',
                                                    queryset=counters_qs,
                                                    to_attr='recent')),
                         to_attr='sources'),
            )
        )

        for accounting_profile in accounting_profiles:
            # Same selection as get_current_bandwidth_profile(), but
            # computed from the prefetched rows instead of one query
            # per profile. The model's effective_date is a DateField
            # (default=timezone.now is stored as a date), so compare
            # date-wise to match the SQL date/timestamp cast.
            candidates = [
                b for b in accounting_profile.bandwidthprofile_set.all()
                if b.effective_date is not None and b.effective_date <= now.date()
            ]
            bandwidth_profile = (
                max(candidates, key=lambda b: b.effective_date)
                if candidates else None
            )

            if bandwidth_profile is not None:
                v = {}
                v['id'] = accounting_profile.id
                v['member_name'] = accounting_profile.member.name
                v['member_name_slug'] = re.sub(r'[ -./\'\(\)]+', '', accounting_profile.member.name)
                v['traffic_cap'] = bandwidth_profile.traffic_cap
                v['burst_limit'] = bandwidth_profile.burst_limit
                v['billable'] = bandwidth_profile.billable
                v['accounting_sources'] = []

                contacts = []
                for site in accounting_profile.member.sites.all():
                    for c in site.contacts.all():
                        if c.role.name == "Network":
                            contacts.append(c.contact.email)
                v['contacts'] = contacts

                for accounting_source in accounting_profile.sources:
                    t = {}
                    t['device'] = accounting_source.device.name
                    t['name'] = accounting_source.name
                    t['destination'] = accounting_source.destination
                    t['current_rate'] = self._current_rate(accounting_source)
                    v['accounting_sources'].append(t)

                results.append(v)

        return Response(results)
