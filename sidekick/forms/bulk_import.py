from django.utils.translation import gettext_lazy as _

from dcim.models import Device, Interface, Site
from netbox.forms import NetBoxModelImportForm
from tenancy.models import Tenant
from utilities.forms.fields import CSVModelChoiceField, SlugField

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


class LogicalSystemImportForm(NetBoxModelImportForm):
    slug = SlugField()

    class Meta:
        model = LogicalSystem
        fields = ('name', 'slug', 'tags')


class RoutingTypeImportForm(NetBoxModelImportForm):
    slug = SlugField()

    class Meta:
        model = RoutingType
        fields = ('name', 'slug', 'tags')


class NetworkServiceTypeImportForm(NetBoxModelImportForm):
    slug = SlugField()

    class Meta:
        model = NetworkServiceType
        fields = ('name', 'slug', 'description', 'tags')


class NetworkServiceImportForm(NetBoxModelImportForm):
    network_service_type = CSVModelChoiceField(
        label=_('Service type'),
        queryset=NetworkServiceType.objects.all(),
        to_field_name='pk',
    )
    member = CSVModelChoiceField(
        label=_('Member'),
        queryset=Tenant.objects.all(),
        required=False,
        to_field_name='pk',
    )
    member_site = CSVModelChoiceField(
        label=_('Member site'),
        queryset=Site.objects.all(),
        required=False,
        to_field_name='pk',
    )
    backup_for = CSVModelChoiceField(
        label=_('Backup for'),
        queryset=NetworkService.objects.all(),
        required=False,
        to_field_name='pk',
    )
    accounting_profile = CSVModelChoiceField(
        label=_('Accounting profile'),
        queryset=AccountingProfile.objects.all(),
        required=False,
        to_field_name='pk',
    )

    class Meta:
        model = NetworkService
        fields = (
            'name', 'network_service_type', 'member', 'member_site', 'legacy_id',
            'start_date', 'end_date', 'description', 'comments', 'active',
            'backup_for', 'accounting_profile', 'tags',
        )


class NetworkServiceDeviceImportForm(NetBoxModelImportForm):
    network_service = CSVModelChoiceField(
        label=_('Network service'),
        queryset=NetworkService.objects.all(),
        to_field_name='pk',
    )
    device = CSVModelChoiceField(
        label=_('Device'),
        queryset=Device.objects.all(),
        to_field_name='pk',
    )

    class Meta:
        model = NetworkServiceDevice
        fields = (
            'network_service', 'device', 'interface', 'vlan', 'comments',
            'legacy_id', 'tags',
        )


class NetworkServiceL2ImportForm(NetBoxModelImportForm):
    network_service_device = CSVModelChoiceField(
        label=_('Network service device'),
        queryset=NetworkServiceDevice.objects.all(),
        to_field_name='pk',
    )

    class Meta:
        model = NetworkServiceL2
        fields = ('network_service_device', 'vlan', 'comments', 'legacy_id', 'tags')


class NetworkServiceL3ImportForm(NetBoxModelImportForm):
    network_service_device = CSVModelChoiceField(
        label=_('Network service device'),
        queryset=NetworkServiceDevice.objects.all(),
        to_field_name='pk',
    )
    member = CSVModelChoiceField(
        label=_('Member'),
        queryset=Tenant.objects.all(),
        required=False,
        to_field_name='pk',
    )
    logical_system = CSVModelChoiceField(
        label=_('Logical system'),
        queryset=LogicalSystem.objects.all(),
        required=False,
        to_field_name='pk',
    )
    routing_type = CSVModelChoiceField(
        label=_('Routing type'),
        queryset=RoutingType.objects.all(),
        required=False,
        to_field_name='pk',
    )
    member_site = CSVModelChoiceField(
        label=_('Member site'),
        queryset=Site.objects.all(),
        required=False,
        to_field_name='pk',
    )

    class Meta:
        model = NetworkServiceL3
        fields = (
            'network_service_device', 'member', 'member_site', 'logical_system',
            'routing_type', 'asn', 'ipv4_unicast', 'ipv4_multicast',
            'provider_router_address_ipv4', 'member_router_address_ipv4',
            'ipv6_unicast', 'ipv6_multicast', 'provider_router_address_ipv6',
            'member_router_address_ipv6', 'active', 'comments', 'legacy_id', 'tags',
        )


class NetworkServiceGroupImportForm(NetBoxModelImportForm):
    slug = SlugField()
    network_services = CSVModelChoiceField(
        label=_('Network services'),
        queryset=NetworkService.objects.all(),
        required=False,
        to_field_name='pk',
    )

    class Meta:
        model = NetworkServiceGroup
        fields = ('name', 'slug', 'description', 'network_services', 'tags')


class AccountingSourceImportForm(NetBoxModelImportForm):
    device = CSVModelChoiceField(
        label=_('Device'),
        queryset=Device.objects.all(),
        to_field_name='pk',
    )

    class Meta:
        model = AccountingSource
        fields = ('device', 'name', 'destination', 'tags')


class AccountingProfileImportForm(NetBoxModelImportForm):
    member = CSVModelChoiceField(
        label=_('Member'),
        queryset=Tenant.objects.all(),
        to_field_name='pk',
    )
    accounting_sources = CSVModelChoiceField(
        label=_('Accounting sources'),
        queryset=AccountingSource.objects.all(),
        required=False,
        to_field_name='pk',
    )

    class Meta:
        model = AccountingProfile
        fields = ('member', 'name', 'enabled', 'accounting_sources', 'comments', 'tags')


class BandwidthProfileImportForm(NetBoxModelImportForm):
    accounting_profile = CSVModelChoiceField(
        label=_('Accounting profile'),
        queryset=AccountingProfile.objects.all(),
        to_field_name='pk',
    )

    class Meta:
        model = BandwidthProfile
        fields = (
            'accounting_profile', 'effective_date', 'traffic_cap', 'burst_limit',
            'billable', 'comments', 'tags',
        )


class NICImportForm(NetBoxModelImportForm):
    interface = CSVModelChoiceField(
        label=_('Interface'),
        queryset=Interface.objects.all(),
        to_field_name='pk',
    )

    class Meta:
        model = NIC
        fields = (
            'interface', 'admin_status', 'oper_status', 'out_rate', 'in_rate',
            'out_octets', 'in_octets', 'out_unicast_packets', 'in_unicast_packets',
            'out_nunicast_packets', 'in_nunicast_packets', 'out_errors', 'in_errors',
            'tags',
        )
