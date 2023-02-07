from django import forms

from netbox.forms import NetBoxModelForm

from utilities.forms import (
    DatePicker,
)

from sidekick.models import (
    LogicalSystem,
    NetworkService,
    NetworkServiceDevice,
    NetworkServiceGroup,
    NetworkServiceL2,
    NetworkServiceL3,
    NetworkServiceType,
    RoutingType,
)


class LogicalSystemForm(NetBoxModelForm):
    class Meta:
        model = LogicalSystem
        fields = ('name',)


class RoutingTypeForm(NetBoxModelForm):
    class Meta:
        model = RoutingType
        fields = ('name',)


class NetworkServiceTypeForm(NetBoxModelForm):
    class Meta:
        model = NetworkServiceType
        fields = ('name',)


class NetworkServiceForm(NetBoxModelForm):
    start_date = forms.DateTimeField(
        required=True,
        label="Start Date",
        widget=DatePicker,
    )

    class Meta:
        model = NetworkService
        fields = ('name', 'network_service_type', 'member', 'member_site', 'legacy_id',
                  'start_date', 'end_date', 'description', 'comments', 'active',
                  'backup_for', 'accounting_profile',)


class NetworkServiceDeviceForm(NetBoxModelForm):
    class Meta:
        model = NetworkServiceDevice
        fields = ('network_service', 'device', 'interface', 'vlan', 'comments', 'legacy_id',)


class NetworkServiceL2Form(NetBoxModelForm):
    class Meta:
        model = NetworkServiceL2
        fields = ('network_service_device', 'vlan', 'comments', 'legacy_id',)


class NetworkServiceL3Form(NetBoxModelForm):
    class Meta:
        model = NetworkServiceL3
        fields = ('member', 'member_site',
                  'network_service_device', 'logical_system', 'routing_type', 'asn',
                  'ipv4_unicast', 'ipv4_multicast', 'ipv4_prefixes',
                  'provider_router_address_ipv4', 'member_router_address_ipv4',
                  'ipv6_unicast', 'ipv6_multicast', 'ipv6_prefixes',
                  'provider_router_address_ipv6', 'member_router_address_ipv6',
                  'comments', 'legacy_id', 'active',)


class NetworkServiceGroupForm(NetBoxModelForm):
    class Meta:
        model = NetworkServiceGroup
        fields = ('name', 'slug', 'description', 'network_services',)
