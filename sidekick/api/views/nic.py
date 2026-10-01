from rest_framework.permissions import IsAuthenticated
from rest_framework.generics import ListAPIView

from netbox.api.authentication import TokenAuthentication

from sidekick.api.serializers import NICSerializer
from sidekick.models import NIC


class NICListView(ListAPIView):
    """
    List the NIC entries for a device, most recent entry per interface.

    Supports an optional ``name`` query parameter to return the full history
    of a single interface instead.
    """
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = NICSerializer
    pagination_class = None

    def get_queryset(self):
        device = self.kwargs.get('device', None)
        if device is not None:
            nics = (NIC.objects
                    .select_related('interface', 'interface__device')
                    .filter(interface__device__id=device))

            name = self.request.query_params.get('name', None)
            if name is not None:
                nics = nics.filter(interface__name=name).order_by('-last_updated')
                return nics

            # Without a name filter, return the most recent NIC entry
            # per interface. NIC keeps up to 5 history rows per interface,
            # so a plain filter would return ~5x the number of interfaces
            # (e.g. 7,206 rows for a core router instead of 1,442).
            # select_related also prevents an N+1 in the serializer
            # (StringRelatedField / description access the interface FK).
            nics = (nics
                    .order_by('interface_id', '-last_updated')
                    .distinct('interface_id'))

            return nics
