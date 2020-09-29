import django_filters

from django.db.models import Q

from netbox_sidekick.models import (
    NIC
)


class NICFilterSet(django_filters.FilterSet):
    q = django_filters.CharFilter(
        method='search',
        label='Search',
    )

    class Meta:
        model = NIC
        fields = ['interface__device']

    def __init(self, data=None, queryset=None, *, request=None, prefix=None):
        super().__init__(
            data=data, queryset=queryset, request=request, prefix=prefix)
        self.filters['device'].field.widget.attrs_update(
            {'class': 'netbox-select2-static'})

    def search(self, queryset, name, value):
        if not value.strip():
            return queryset
        return queryset.filter(
            Q(interface__name__icontains=value)
        ).distinct()
