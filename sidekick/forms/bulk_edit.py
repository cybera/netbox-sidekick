from django import forms
from django.utils.translation import gettext_lazy as _

from netbox.forms import NetBoxModelBulkEditForm
from utilities.forms.fields import DynamicModelChoiceField
from utilities.forms.widgets import BulkEditNullBooleanSelect

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
    active = forms.NullBooleanField(
        label=_('Active'),
        required=False,
        widget=BulkEditNullBooleanSelect,
    )
    start_date = forms.DateField(
        label=_('Start date'),
        required=False,
    )
    end_date = forms.DateField(
        label=_('End date'),
        required=False,
    )
    description = forms.CharField(
        label=_('Description'),
        required=False,
    )
    comments = forms.CharField(
        label=_('Comments'),
        required=False,
    )

    model = NetworkService
    nullable_fields = (
        'network_service_type', 'member', 'member_site', 'backup_for',
        'accounting_profile', 'start_date', 'end_date', 'description', 'comments',
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
    interface = forms.CharField(
        label=_('Interface'),
        required=False,
    )
    vlan = forms.IntegerField(
        label=_('VLAN'),
        required=False,
    )
    comments = forms.CharField(
        label=_('Comments'),
        required=False,
    )

    model = NetworkServiceDevice
    nullable_fields = ('network_service', 'device', 'interface', 'vlan', 'comments')


class NetworkServiceL2BulkEditForm(NetBoxModelBulkEditForm):
    vlan = forms.IntegerField(
        label=_('VLAN'),
        required=False,
    )
    comments = forms.CharField(
        label=_('Comments'),
        required=False,
    )

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
    asn = forms.CharField(
        label=_('ASN'),
        required=False,
    )
    active = forms.NullBooleanField(
        label=_('Active'),
        required=False,
        widget=BulkEditNullBooleanSelect,
    )
    comments = forms.CharField(
        label=_('Comments'),
        required=False,
    )

    model = NetworkServiceL3
    nullable_fields = (
        'member', 'member_site', 'logical_system', 'routing_type', 'asn', 'comments',
    )


class NetworkServiceGroupBulkEditForm(NetBoxModelBulkEditForm):
    description = forms.CharField(
        label=_('Description'),
        required=False,
    )

    model = NetworkServiceGroup
    nullable_fields = ('description',)


class AccountingSourceBulkEditForm(NetBoxModelBulkEditForm):
    device = DynamicModelChoiceField(
        label=_('Device'),
        queryset=Device.objects.all(),
        required=False,
    )
    destination = forms.CharField(
        label=_('Destination'),
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
    name = forms.CharField(
        label=_('Name'),
        required=False,
    )
    enabled = forms.NullBooleanField(
        label=_('Enabled'),
        required=False,
        widget=BulkEditNullBooleanSelect,
    )
    comments = forms.CharField(
        label=_('Comments'),
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
    traffic_cap = forms.IntegerField(
        label=_('Traffic cap'),
        required=False,
    )
    burst_limit = forms.IntegerField(
        label=_('Burst limit'),
        required=False,
    )
    billable = forms.NullBooleanField(
        label=_('Billable'),
        required=False,
        widget=BulkEditNullBooleanSelect,
    )
    comments = forms.CharField(
        label=_('Comments'),
        required=False,
    )

    model = BandwidthProfile
    nullable_fields = ('accounting_profile', 'traffic_cap', 'burst_limit', 'comments')


class NICBulkEditForm(NetBoxModelBulkEditForm):
    interface = DynamicModelChoiceField(
        label=_('Interface'),
        queryset=Interface.objects.all(),
        required=False,
    )
    admin_status = forms.NullBooleanField(
        label=_('Admin status'),
        required=False,
        widget=BulkEditNullBooleanSelect,
    )
    oper_status = forms.NullBooleanField(
        label=_('Oper status'),
        required=False,
        widget=BulkEditNullBooleanSelect,
    )

    model = NIC
    nullable_fields = ('interface', 'admin_status', 'oper_status')
