from netbox.api.serializers import NetBoxModelSerializer
from rest_framework import serializers

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


class LogicalSystemSerializer(NetBoxModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='plugins-api:sidekick-api:logicalsystem-detail')

    class Meta:
        model = LogicalSystem
        fields = ('url', 'name', 'slug',)


class RoutingTypeSerializer(NetBoxModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='plugins-api:sidekick-api:routingtype-detail')

    class Meta:
        model = RoutingType
        fields = ('url', 'name', 'slug',)


class NetworkServiceTypeSerializer(NetBoxModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='plugins-api:sidekick-api:networkservicetype-detail')

    class Meta:
        model = NetworkServiceType
        fields = ('url', 'name', 'slug', 'description',)


class NetworkServiceSerializer(NetBoxModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='plugins-api:sidekick-api:networkservice-detail')

    class Meta:
        model = NetworkService
        fields = (
            'url', 'name', 'network_service_type', 'member', 'member_site', 'legacy_id',
            'start_date', 'end_date', 'description', 'comments', 'active',
            'backup_for', 'accounting_profile')


class NetworkServiceDeviceSerializer(NetBoxModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='plugins-api:sidekick-api:networkservicedevice-detail')

    class Meta:
        model = NetworkServiceDevice
        fields = (
            'url', 'network_service', 'device', 'interface', 'vlan', 'comments', 'legacy_id',)


class NetworkServiceL2Serializer(NetBoxModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='plugins-api:sidekick-api:networkservicel2-detail')

    class Meta:
        model = NetworkServiceL2
        fields = (
            'url', 'network_service_device', 'vlan', 'comments', 'legacy_id',)


class NetworkServiceL3Serializer(NetBoxModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='plugins-api:sidekick-api:networkservicel3-detail')

    class Meta:
        model = NetworkServiceL3
        fields = (
            'url', 'network_service_device', 'logical_system', 'routing_type', 'asn',
            'ipv4_unicast', 'ipv4_multicast', 'provider_router_address_ipv4',
            'member_router_address_ipv4', 'ipv6_unicast', 'ipv6_multicast',
            'ip_prefixes', 'provider_router_address_ipv6', 'member_router_address_ipv6',
            'comments', 'legacy_id',)


class NetworkServiceGroupSerializer(NetBoxModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='plugins-api:sidekick-api:networkservicegroup-detail')

    class Meta:
        model = NetworkServiceGroup
        fields = (
            'url', 'name', 'slug', 'description', 'network_services',)
