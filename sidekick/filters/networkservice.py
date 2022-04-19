import django_filters
import netaddr

from django import forms

from netbox.filtersets import NetBoxModelFilterSet
from netbox.forms import NetBoxModelFilterSetForm
from tenancy.models import Tenant
from utilities.forms import (
    BOOLEAN_WITH_BLANK_CHOICES,
    DynamicModelMultipleChoiceField,
    StaticSelect,
)

from sidekick.models import (
    RoutingType, LogicalSystem,
    NetworkServiceType,
    NetworkService,
    NetworkServiceGroup,
)


class LogicalSystemFilterSet(NetBoxModelFilterSet):
    class Meta:
        model = LogicalSystem
        fields = ('name',)


class LogicalSystemFilterSetForm(NetBoxModelFilterSetForm):
    model = LogicalSystem


class RoutingTypeFilterSet(NetBoxModelFilterSet):
    class Meta:
        model = RoutingType
        fields = ('name',)


class RoutingTypeFilterSetForm(NetBoxModelFilterSetForm):
    model = RoutingType


class NetworkServiceTypeFilterSet(NetBoxModelFilterSet):
    class Meta:
        model = NetworkServiceType
        fields = ('name',)


class NetworkServiceTypeFilterSetForm(NetBoxModelFilterSetForm):
    model = NetworkServiceType


class NetworkServiceFilterSet(NetBoxModelFilterSet):
    ip_address = django_filters.CharFilter(
        method='prefix_search',
        label='IP Address',
    )

    class Meta:
        model = NetworkService
        fields = ('member', 'member_site', 'network_service_type', 'active')

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


class NetworkServiceFilterSetForm(NetBoxModelFilterSetForm):
    model = NetworkService

    member = DynamicModelMultipleChoiceField(
        queryset=Tenant.objects.filter(group__name='Members'),
        required=False,
        label='Member',
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


class NetworkServiceGroupFilterSetForm(NetBoxModelFilterSetForm):
    model = NetworkServiceGroup
