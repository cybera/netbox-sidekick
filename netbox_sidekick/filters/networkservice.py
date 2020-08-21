import django_filters

from django.db.models import Q

from netbox_sidekick.models import (
    LogicalSystem, NetworkServiceType,
    NetworkService, RoutingType
)


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

    class Meta:
        model = NetworkService
        fields = ['device', 'logical_system', 'member', 'network_service_type']

    def __init__(self, data=None, queryset=None, *, request=None, prefix=None):
        super(NetworkServiceFilterSet, self).__init__(
            data=data, queryset=queryset, request=request, prefix=prefix)
        self.filters['device'].field.widget.attrs.update(
            {'class': 'netbox-select2-static'})
        self.filters['logical_system'].field.widget.attrs.update(
            {'class': 'netbox-select2-static'})
        self.filters['member'].field.widget.attrs.update(
            {'class': 'netbox-select2-static'})
        self.filters['network_service_type'].field.widget.attrs.update(
            {'class': 'netbox-select2-static'})

    def search(self, queryset, name, value):
        if not value.strip():
            return queryset
        return queryset.filter(
            Q(name__icontains=value) |
            Q(comments__icontains=value) |
            Q(description__icontains=value)
        ).distinct()
