from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from decimal import Decimal

from django.shortcuts import get_object_or_404

from netbox.api.authentication import TokenAuthentication
from netbox.api.viewsets import NetBoxModelViewSet

from tenancy.models import Tenant

from sidekick.api.serializers import TransitRateSerializer
from sidekick.filtersets import TransitRateFilterSet
from sidekick.models import TransitRate
from sidekick.utils.billing import member_billing


class TransitRateViewSet(NetBoxModelViewSet):
    queryset = TransitRate.objects.all()
    serializer_class = TransitRateSerializer
    filterset_class = TransitRateFilterSet


class MemberBillingView(APIView):
    """
    The resolved transit bill for one member: billable cap times the rate in force.

    Reports which rate applied (`rate_source`: `member override`, `global default`,
    or `fallback`) and the effective date it came from, because a bill computed
    against a fallback constant looks identical to a correct one otherwise.

    Read-only. `?as_of=YYYY-MM-DD` prices the member on a past date using the caps
    and rate that were in force then.
    """

    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]

    def get(self, request, member):
        tenant = get_object_or_404(Tenant, pk=member)
        as_of = request.query_params.get('as_of') or None
        billing = member_billing(tenant, as_of=as_of)
        billing['cap_mbit'] = int(billing['cap_mbit'])
        billing['rate_per_mbit'] = str(billing['rate_per_mbit'])
        billing['monthly_cost'] = str(billing['monthly_cost'].quantize(Decimal('0.01')))
        billing['as_of'] = str(billing['as_of'])
        billing['rate_effective_date'] = (
            str(billing['rate_effective_date']) if billing['rate_effective_date'] else None)
        return Response(billing)
