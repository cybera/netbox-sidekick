import django_filters

from django.db.models import Q

from netbox_sidekick.models import (
    RoutingType, LogicalSystem,
    NetworkServiceType,
    NetworkService,
    NetworkServiceGroup,
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
        fields = ['member', 'member_site', 'network_service_type', 'active']

    def __init__(self, data=None, queryset=None, *, request=None, prefix=None):
        super().__init__(
            data=data, queryset=queryset, request=request, prefix=prefix)
        self.filters['member'].field.widget.attrs.update(
            {'class': 'netbox-select2-static form-control'})
        self.filters['member_site'].field.widget.attrs.update(
            {'class': 'netbox-select2-static form-control'})
        self.filters['active'].field.widget.attrs.update(
            {'class': 'netbox-select2-static form-control'})
        self.filters['network_service_type'].field.widget.attrs.update(
            {'class': 'netbox-select2-static form-control'})

    def search(self, queryset, name, value):
        if not value.strip():
            return queryset
        return queryset.filter(
            Q(name__icontains=value) |
            Q(comments__icontains=value) |
            Q(description__icontains=value)
        ).distinct()

    @property
    def qs(self):
        parent = super().qs
        active = self.request.GET.get('active', 'true')
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
