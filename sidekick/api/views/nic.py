from rest_framework.permissions import IsAuthenticated
from rest_framework.generics import ListAPIView

from netbox.api.authentication import TokenAuthentication

from sidekick.api.serializers import NICSerializer
from sidekick.models import NIC


class NICListView(ListAPIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = NICSerializer
    pagination_class = None

    def get_queryset(self):
        device = self.kwargs.get('device', None)
        if device is not None:
            nics = NIC.objects.filter(interface__device__id=device).order_by('-last_updated')

            name = self.request.query_params.get('name', None)
            if name is not None:
                nics = nics.filter(interface__name=name).order_by('-last_updated')

            return nics
