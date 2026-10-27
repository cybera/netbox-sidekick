from dcim.api.serializers import DeviceSerializer, SiteSerializer
from netbox.api.serializers import NetBoxModelSerializer
from rest_framework import serializers
from tenancy.api.serializers import TenantSerializer
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

# Serializer conventions in this module, matching core NetBox:
#
# - `id` and `display` are always present. Core NetBox endpoints publish both, and
#   omitting `id` forced every consumer to parse the trailing segment of `url`.
# - Foreign keys render as brief nested objects on read and accept a primary key on
#   write (`nested=True`). Before 2026-10-27 they rendered as bare integers, so a
#   consumer needed a second request per relation.
# - `brief_fields` is declared explicitly so a nested relation cannot recurse
#   further than one level, and so the brief payload stays small.
# - Self-referential and M2M list fields stay as primary keys: `backup_for` would
#   recurse, `ip_prefixes` / `accounting_sources` are lists, and `accounting_profile`
#   is a heavy object (M2M to sources) whose nesting would bloat every service row.


class LogicalSystemSerializer(NetBoxModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='plugins-api:sidekick-api:logicalsystem-detail')

    class Meta:
        model = LogicalSystem
        fields = ('id', 'url', 'display', 'name', 'slug',)
        brief_fields = ('id', 'url', 'display', 'name', 'slug',)


class RoutingTypeSerializer(NetBoxModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='plugins-api:sidekick-api:routingtype-detail')

    class Meta:
        model = RoutingType
        fields = ('id', 'url', 'display', 'name', 'slug',)
        brief_fields = ('id', 'url', 'display', 'name', 'slug',)


class NetworkServiceTypeSerializer(NetBoxModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='plugins-api:sidekick-api:networkservicetype-detail')

    class Meta:
        model = NetworkServiceType
        fields = ('id', 'url', 'display', 'name', 'slug', 'description',)
        brief_fields = ('id', 'url', 'display', 'name', 'slug',)


class NetworkServiceSerializer(NetBoxModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='plugins-api:sidekick-api:networkservice-detail')
    # These three are NOT NULL on the model, so the serializer must not advertise
    # them as nullable: `allow_null` here would make the API schema lie and turn a
    # missing member into a 400 at the database instead of at validation.
    network_service_type = NetworkServiceTypeSerializer(nested=True)
    member = TenantSerializer(nested=True)
    member_site = SiteSerializer(nested=True)

    class Meta:
        model = NetworkService
        fields = (
            'id', 'url', 'display', 'name', 'network_service_type', 'member', 'member_site',
            'legacy_id', 'start_date', 'end_date', 'description', 'comments', 'active',
            'backup_for', 'accounting_profile')
        brief_fields = ('id', 'url', 'display', 'name', 'legacy_id')


class NetworkServiceDeviceSerializer(NetBoxModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='plugins-api:sidekick-api:networkservicedevice-detail')
    network_service = NetworkServiceSerializer(nested=True, required=False, allow_null=True)
    device = DeviceSerializer(nested=True, required=False, allow_null=True)
    # `interface` is a CharField holding an interface name (e.g. 'irb.27'), not a
    # relation to dcim.Interface. Do not wrap it in a serializer.

    class Meta:
        model = NetworkServiceDevice
        fields = (
            'id', 'url', 'display', 'network_service', 'device', 'interface', 'vlan', 'comments',
            'legacy_id',)
        brief_fields = ('id', 'url', 'display', 'network_service', 'device', 'interface', 'vlan')


class NetworkServiceL2Serializer(NetBoxModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='plugins-api:sidekick-api:networkservicel2-detail')
    network_service_device = NetworkServiceDeviceSerializer(nested=True, required=False, allow_null=True)

    class Meta:
        model = NetworkServiceL2
        fields = (
            'id', 'url', 'display', 'network_service_device', 'vlan', 'comments', 'legacy_id',)
        brief_fields = ('id', 'url', 'display', 'vlan')


class NetworkServiceL3Serializer(NetBoxModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='plugins-api:sidekick-api:networkservicel3-detail')
    network_service_device = NetworkServiceDeviceSerializer(nested=True, required=False, allow_null=True)
    logical_system = LogicalSystemSerializer(nested=True, required=False, allow_null=True)
    routing_type = RoutingTypeSerializer(nested=True, required=False, allow_null=True)

    class Meta:
        model = NetworkServiceL3
        fields = (
            'id', 'url', 'display', 'network_service_device', 'logical_system', 'routing_type',
            'asn', 'ipv4_unicast', 'ipv4_multicast', 'provider_router_address_ipv4',
            'member_router_address_ipv4', 'ipv6_unicast', 'ipv6_multicast',
            'ip_prefixes', 'provider_router_address_ipv6', 'member_router_address_ipv6',
            'comments', 'legacy_id',)
        brief_fields = (
            'id', 'url', 'display', 'network_service_device', 'asn', 'logical_system',
            'routing_type')


class NetworkServiceGroupSerializer(NetBoxModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='plugins-api:sidekick-api:networkservicegroup-detail')
    network_services = NetworkServiceSerializer(nested=True, many=True, required=False)

    class Meta:
        model = NetworkServiceGroup
        fields = (
            'id', 'url', 'display', 'name', 'slug', 'description', 'network_services',)
        brief_fields = ('id', 'url', 'display', 'name', 'slug')
