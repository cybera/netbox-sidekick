from django import forms
from django.utils.translation import gettext_lazy as _

from netbox.forms import NetBoxModelBulkEditForm
from utilities.forms.fields import DynamicModelChoiceField

from dcim.models import Device, Interface, Site
from tenancy.models import Tenant

from sidekick.models import (
    AccountingProfile,
    AccountingSource,
    BandwidthProfile,
    LogicalSystem,
    NetworkService,
    NetworkServiceDevice,
    NetworkServiceGroup,
    NetworkServiceL2,
    NetworkServiceL3,
    NetworkServiceType,
    NIC,
    RoutingType,
)


class LogicalSystemBulkEditForm(NetBoxModelBulkEditForm):
    model = LogicalSystem
    nullable_fields = ()


class RoutingTypeBulkEditForm(NetBoxModelBulkEditForm):
    model = RoutingType
    nullable_fields = ()


class NetworkServiceTypeBulkEditForm(NetBoxModelBulkEditForm):
    description = forms.CharField(
        label=_('Description'),
        required=False,
    )

    model = NetworkServiceType
    nullable_fields = ('description',)


class NetworkServiceBulkEditForm(NetBoxModelBulkEditForm):
    network_service_type = DynamicModelChoiceField(
        label=_('Service type'),
        queryset=NetworkServiceType.objects.all(),
        required=False,
    )
    member = DynamicModelChoiceField(
        label=_('Member'),
        queryset=Tenant.objects.all(),
        required=False,
    )
    member_site = DynamicModelChoiceField(
        label=_('Member site'),
        queryset=Site.objects.all(),
        required=False,
    )
    backup_for = DynamicModelChoiceField(
        label=_('Backup for'),
        queryset=NetworkService.objects.all(),
        required=False,
    )
    accounting_profile = DynamicModelChoiceField(
        label=_('Accounting profile'),
        queryset=AccountingProfile.objects.all(),
        required=False,
    )

    model = NetworkService
    nullable_fields = (
        'network_service_type', 'member', 'member_site', 'start_date', 'end_date',
        'description', 'comments', 'backup_for', 'accounting_profile',
    )


class NetworkServiceDeviceBulkEditForm(NetBoxModelBulkEditForm):
    network_service = DynamicModelChoiceField(
        label=_('Network service'),
        queryset=NetworkService.objects.all(),
        required=False,
    )
    device = DynamicModelChoiceField(
        label=_('Device'),
        queryset=Device.objects.all(),
        required=False,
    )

    model = NetworkServiceDevice
    nullable_fields = ('network_service', 'device', 'interface', 'vlan', 'comments')


class NetworkServiceL2BulkEditForm(NetBoxModelBulkEditForm):
    model = NetworkServiceL2
    nullable_fields = ('vlan', 'comments')


class NetworkServiceL3BulkEditForm(NetBoxModelBulkEditForm):
    member = DynamicModelChoiceField(
        label=_('Member'),
        queryset=Tenant.objects.all(),
        required=False,
    )
    member_site = DynamicModelChoiceField(
        label=_('Member site'),
        queryset=Site.objects.all(),
        required=False,
    )
    logical_system = DynamicModelChoiceField(
        label=_('Logical system'),
        queryset=LogicalSystem.objects.all(),
        required=False,
    )
    routing_type = DynamicModelChoiceField(
        label=_('Routing type'),
        queryset=RoutingType.objects.all(),
        required=False,
    )

    model = NetworkServiceL3
    nullable_fields = (
        'member', 'member_site', 'logical_system', 'routing_type', 'asn',
        'provider_router_address_ipv4', 'member_router_address_ipv4',
        'provider_router_address_ipv6', 'member_router_address_ipv6', 'comments',
    )


class NetworkServiceGroupBulkEditForm(NetBoxModelBulkEditForm):
    model = NetworkServiceGroup
    nullable_fields = ('description',)


class AccountingSourceBulkEditForm(NetBoxModelBulkEditForm):
    device = DynamicModelChoiceField(
        label=_('Device'),
        queryset=Device.objects.all(),
        required=False,
    )

    model = AccountingSource
    nullable_fields = ('device', 'destination')


class AccountingProfileBulkEditForm(NetBoxModelBulkEditForm):
    member = DynamicModelChoiceField(
        label=_('Member'),
        queryset=Tenant.objects.all(),
        required=False,
    )

    model = AccountingProfile
    nullable_fields = ('member', 'name', 'comments')


class BandwidthProfileBulkEditForm(NetBoxModelBulkEditForm):
    accounting_profile = DynamicModelChoiceField(
        label=_('Accounting profile'),
        queryset=AccountingProfile.objects.all(),
        required=False,
    )

    model = BandwidthProfile
    nullable_fields = ('traffic_cap', 'burst_limit', 'comments')


class NICBulkEditForm(NetBoxModelBulkEditForm):
    interface = DynamicModelChoiceField(
        label=_('Interface'),
        queryset=Interface.objects.all(),
        required=False,
    )

    model = NIC
    nullable_fields = (
        'interface', 'admin_status', 'oper_status', 'out_rate', 'in_rate',
        'out_octets', 'in_octets', 'out_unicast_packets', 'in_unicast_packets',
        'out_nunicast_packets', 'in_nunicast_packets', 'out_errors', 'in_errors',
    )
