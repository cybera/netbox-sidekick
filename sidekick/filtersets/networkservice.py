import django_filters
import netaddr

from django import forms
from django.db.models import Q

from dcim.models import Device
from netbox.filtersets import NetBoxModelFilterSet
from netbox.forms import NetBoxModelFilterSetForm
from tenancy.models import Tenant
from utilities.forms.fields import DynamicModelMultipleChoiceField
from utilities.forms.constants import BOOLEAN_WITH_BLANK_CHOICES
from utilities.forms.widgets import Select as StaticSelect

from sidekick.models import (
    RoutingType, LogicalSystem,
    NetworkServiceType,
    NetworkService,
    NetworkServiceDevice,
    NetworkServiceL2,
    NetworkServiceL3,
    NetworkServiceGroup,
)


class LogicalSystemFilterSet(NetBoxModelFilterSet):
    class Meta:
        model = LogicalSystem
        fields = ('name',)

    def search(self, queryset, name, value):
        if not value.strip():
            return queryset
        return queryset.filter(
            Q(name__icontains=value) |
            Q(slug__icontains=value)
        )


class LogicalSystemFilterSetForm(NetBoxModelFilterSetForm):
    model = LogicalSystem


class RoutingTypeFilterSet(NetBoxModelFilterSet):
    class Meta:
        model = RoutingType
        fields = ('name',)

    def search(self, queryset, name, value):
        if not value.strip():
            return queryset
        return queryset.filter(
            Q(name__icontains=value) |
            Q(slug__icontains=value)
        )


class RoutingTypeFilterSetForm(NetBoxModelFilterSetForm):
    model = RoutingType


class NetworkServiceTypeFilterSet(NetBoxModelFilterSet):
    class Meta:
        model = NetworkServiceType
        fields = ('name',)

    def search(self, queryset, name, value):
        if not value.strip():
            return queryset
        return queryset.filter(
            Q(name__icontains=value) |
            Q(slug__icontains=value) |
            Q(description__icontains=value)
        )


class NetworkServiceTypeFilterSetForm(NetBoxModelFilterSetForm):
    model = NetworkServiceType


class NetworkServiceFilterSet(NetBoxModelFilterSet):
    ip_address = django_filters.CharFilter(
        method='prefix_search',
        label='IP Address',
    )
    member_id = django_filters.ModelMultipleChoiceFilter(
        field_name='member',
        queryset=Tenant.objects.filter(group__name='Members'),
        label='Member (ID)',
    )
    network_service_type_id = django_filters.ModelMultipleChoiceFilter(
        field_name='network_service_type',
        queryset=NetworkServiceType.objects.all(),
        label='Service type (ID)',
    )
    logical_system_id = django_filters.ModelMultipleChoiceFilter(
        field_name='network_service_devices__network_service_l3__logical_system',
        queryset=LogicalSystem.objects.all(),
        distinct=True,
        label='Logical system (ID)',
    )
    routing_type_id = django_filters.ModelMultipleChoiceFilter(
        field_name='network_service_devices__network_service_l3__routing_type',
        queryset=RoutingType.objects.all(),
        distinct=True,
        label='Routing type (ID)',
    )

    class Meta:
        model = NetworkService
        fields = ('member', 'active', 'network_service_type')

    def __init__(self, data, *args, **kwargs):
        if not data.get('active'):
            data = data.copy()
            data['active'] = True
        super().__init__(data, *args, **kwargs)

    def prefix_search(self, queryset, name, value):
        services = []
        if not value.strip():
            return queryset

        if '/' in value:
            try:
                ip = netaddr.IPNetwork(value)
            except netaddr.core.AddrFormatError:
                return queryset
        else:
            try:
                ip = netaddr.IPAddress(value)
            except netaddr.core.AddrFormatError:
                return queryset

        for network_service in NetworkService.objects.filter(active=True):
            for prefix in network_service.get_ip_prefixes():
                prefix = netaddr.IPSet(prefix)
                if ip in prefix:
                    services.append(network_service.id)
                    continue
        return queryset.filter(
            id__in=services
        )

    def search(self, queryset, name, value):
        if not value.strip():
            return queryset
        qs_filter = (
            Q(name__icontains=value) |
            Q(member__name__icontains=value)
        )

        return queryset.filter(qs_filter)


class NetworkServiceFilterSetForm(NetBoxModelFilterSetForm):
    model = NetworkService

    member = DynamicModelMultipleChoiceField(
        queryset=Tenant.objects.filter(group__name='Members'),
        required=False,
        label='Member',
    )

    network_service_type = DynamicModelMultipleChoiceField(
        queryset=NetworkServiceType.objects.all(),
        required=False,
        label='Service Type',
    )

    ip_address = forms.CharField(
        required=False,
        label='IP Address',
    )

    active = forms.NullBooleanField(
        required=False,
        label='Active?',
        widget=StaticSelect(
            choices=BOOLEAN_WITH_BLANK_CHOICES,
        )
    )


class NetworkServiceGroupFilterSet(NetBoxModelFilterSet):
    class Meta:
        model = NetworkServiceGroup
        fields = ('network_services',)

    def search(self, queryset, name, value):
        if not value.strip():
            return queryset
        return queryset.filter(
            Q(name__icontains=value) |
            Q(slug__icontains=value) |
            Q(description__icontains=value)
        )


class NetworkServiceGroupFilterSetForm(NetBoxModelFilterSetForm):
    model = NetworkServiceGroup


class NetworkServiceL3FilterSet(NetBoxModelFilterSet):
    member_id = django_filters.ModelMultipleChoiceFilter(
        field_name='member',
        queryset=Tenant.objects.filter(group__name='Members'),
        label='Member (ID)',
    )
    logical_system_id = django_filters.ModelMultipleChoiceFilter(
        field_name='logical_system',
        queryset=LogicalSystem.objects.all(),
        label='Logical system (ID)',
    )
    routing_type_id = django_filters.ModelMultipleChoiceFilter(
        field_name='routing_type',
        queryset=RoutingType.objects.all(),
        label='Routing type (ID)',
    )
    network_service_device_id = django_filters.ModelMultipleChoiceFilter(
        field_name='network_service_device',
        queryset=NetworkServiceDevice.objects.all(),
        label='Network service device (ID)',
    )

    class Meta:
        model = NetworkServiceL3
        fields = ('member', 'active', 'logical_system', 'routing_type',
                  'network_service_device')

    def search(self, queryset, name, value):
        if not value.strip():
            return queryset
        return queryset.filter(
            Q(name__icontains=value) |
            Q(member__name__icontains=value)
        )


class NetworkServiceL3FilterSetForm(NetBoxModelFilterSetForm):
    model = NetworkServiceL3

    logical_system = DynamicModelMultipleChoiceField(
        queryset=LogicalSystem.objects.all(),
        required=False,
        label='Logical System',
    )

    routing_type = DynamicModelMultipleChoiceField(
        queryset=RoutingType.objects.all(),
        required=False,
        label='Routing Type',
    )

    network_service_device = DynamicModelMultipleChoiceField(
        queryset=NetworkServiceDevice.objects.all(),
        required=False,
        label='Network Service Device',
    )


class PeeringConnectionFilterSet(NetBoxModelFilterSet):
    member_id = django_filters.ModelMultipleChoiceFilter(
        field_name='member',
        queryset=Tenant.objects.filter(group__name='Members'),
        label='Member (ID)',
    )

    class Meta:
        model = NetworkServiceL3
        fields = ('member', 'active')

    def search(self, queryset, name, value):
        if not value.strip():
            return queryset
        return queryset.filter(
            Q(name__icontains=value) |
            Q(member__name__icontains=value)
        )


class PeeringConnectionFilterSetForm(NetBoxModelFilterSetForm):
    model = NetworkServiceL3


class NetworkServiceDeviceFilterSet(NetBoxModelFilterSet):
    network_service_id = django_filters.ModelMultipleChoiceFilter(
        field_name='network_service',
        queryset=NetworkService.objects.all(),
        label='Network service (ID)',
    )
    device_id = django_filters.ModelMultipleChoiceFilter(
        field_name='device',
        queryset=Device.objects.all(),
        label='Device (ID)',
    )

    class Meta:
        model = NetworkServiceDevice
        fields = ('network_service', 'device')

    def search(self, queryset, name, value):
        if not value.strip():
            return queryset
        return queryset.filter(
            Q(network_service__name__icontains=value) |
            Q(device__name__icontains=value) |
            Q(interface__icontains=value)
        )


class NetworkServiceDeviceFilterSetForm(NetBoxModelFilterSetForm):
    model = NetworkServiceDevice

    network_service = DynamicModelMultipleChoiceField(
        queryset=NetworkService.objects.all(),
        required=False,
        label='Network Service',
    )

    device = DynamicModelMultipleChoiceField(
        queryset=Device.objects.all(),
        required=False,
        label='Device',
    )


class NetworkServiceL2FilterSet(NetBoxModelFilterSet):
    network_service_device_id = django_filters.ModelMultipleChoiceFilter(
        field_name='network_service_device',
        queryset=NetworkServiceDevice.objects.all(),
        label='Network service device (ID)',
    )

    class Meta:
        model = NetworkServiceL2
        fields = ('network_service_device', 'vlan')

    def search(self, queryset, name, value):
        if not value.strip():
            return queryset
        return queryset.filter(
            Q(network_service_device__network_service__name__icontains=value) |
            Q(network_service_device__device__name__icontains=value)
        )


class NetworkServiceL2FilterSetForm(NetBoxModelFilterSetForm):
    model = NetworkServiceL2

    network_service_device = DynamicModelMultipleChoiceField(
        queryset=NetworkServiceDevice.objects.all(),
        required=False,
        label='Network Service Device',
    )
