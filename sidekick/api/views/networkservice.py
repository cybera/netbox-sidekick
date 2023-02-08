from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.renderers import JSONRenderer
from rest_framework.views import APIView

from netbox.api.authentication import TokenAuthentication
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
