from netbox.api.viewsets import NetBoxModelViewSet

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
