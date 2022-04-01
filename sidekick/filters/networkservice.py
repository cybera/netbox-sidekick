import django_filters

import netaddr

from django.core.validators import EMPTY_VALUES
from django.db.models import Q

from sidekick.models import (
    RoutingType, LogicalSystem,
    NetworkServiceType,
    NetworkService,
    NetworkServiceGroup,
)


class EmptyStringFilter(django_filters.BooleanFilter):
    def filter(self, qs, value):
        if value in EMPTY_VALUES:
            return qs

        exclude = self.exclude ^ (value is False)
        method = qs.exclude if exclude else qs.filter
        return method(**{self.field_name: True})


class LogicalSystemFilterSet(django_filters.FilterSet):
    q = django_filters.CharFilter(
        method='search',
        label='Search',
    )

    class Meta:
        model = LogicalSystem
        fields = []

    def search(self, queryset, name, value):
        if not value.strip():
            return queryset
        return queryset.filter(
            Q(name__icontains=value)
        ).distinct()


class RoutingTypeFilterSet(django_filters.FilterSet):
    q = django_filters.CharFilter(
        method='search',
        label='Search',
    )

    class Meta:
        model = RoutingType
        fields = []

    def search(self, queryset, name, value):
        if not value.strip():
            return queryset
        return queryset.filter(
            Q(name__icontains=value)
        ).distinct()


class NetworkServiceTypeFilterSet(django_filters.FilterSet):
    q = django_filters.CharFilter(
        method='search',
        label='Search',
    )

    class Meta:
        model = NetworkServiceType
        fields = []

    def search(self, queryset, name, value):
        if not value.strip():
            return queryset
        return queryset.filter(
            Q(name__icontains=value) |
            Q(description__icontains=value)
        ).distinct()


class NetworkServiceFilterSet(django_filters.FilterSet):
    q = django_filters.CharFilter(
        method='search',
        label='Search',
    )

    ip_address = django_filters.CharFilter(
        method='prefix_search',
        label='IP Address',
    )

    active = EmptyStringFilter(field_name='active')

    class Meta:
        model = NetworkService
        fields = ['member', 'member_site', 'network_service_type', 'ip_address', 'active']

    def __init__(self, data=None, queryset=None, *, request=None, prefix=None):
        super().__init__(
            data=data, queryset=queryset, request=request, prefix=prefix)
        self.filters['ip_address'].field.widget.attrs.update(
            {'class': 'form-control'})
        self.filters['member'].field.widget.attrs.update(
            {'class': 'netbox-select2-static form-control'})
        self.filters['member_site'].field.widget.attrs.update(
            {'class': 'netbox-select2-static form-control'})
        self.filters['active'].field.widget.attrs.update(
            {'class': 'netbox-select2-static form-control'})
        self.filters['network_service_type'].field.widget.attrs.update(
            {'class': 'netbox-select2-static form-control'})
        self.form.initial['active'] = True

    def search(self, queryset, name, value):
        if not value.strip():
            return queryset
        return queryset.filter(
            Q(name__icontains=value) |
            Q(comments__icontains=value) |
            Q(description__icontains=value)
        ).distinct()

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

    @property
    def qs(self):
        parent = super().qs
        active = self.request.GET.get('active', 'true')
        if active.lower() == 'unknown':
            return parent.filter()

        if active.lower() == 'false':
            active = False
        else:
            active = True
        return parent.filter(active=active)


class NetworkServiceGroupFilterSet(django_filters.FilterSet):
    q = django_filters.CharFilter(
        method='search',
        label='Search',
    )

    class Meta:
        model = NetworkServiceGroup
        fields = ['network_services']

    def __init__(self, data=None, queryset=None, *, request=None, prefix=None):
        super().__init__(
            data=data, queryset=queryset, request=request, prefix=prefix)
        self.filters['network_services'].field.widget.attrs.update(
            {'class': 'netbox-select2-static form-control'})

    def search(self, queryset, name, value):
        if not value.strip():
            return queryset
        return queryset.filter(
            Q(name__icontains=value) |
            Q(description__icontains=value) |
            Q(network_services__name__icontains=value)
        ).distinct()
