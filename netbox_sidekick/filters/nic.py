import django_filters

from django.db.models import Q

from dcim.models import Device

from netbox_sidekick.models import (
    NIC
)


def devices(request):
    devices = NIC.objects.order_by('interface__device__name').distinct(
        'interface__device__name').values_list('interface__device__id', flat=True)
    return Device.objects.filter(pk__in=devices)


class NICFilterSet(django_filters.FilterSet):
    q = django_filters.CharFilter(
        method='search',
        label='Search',
    )

    device = django_filters.ModelChoiceFilter(
        label='Device',
        field_name='device',
        method='filter_device',
        queryset=devices,
    )

    class Meta:
        model = NIC
        fields = ['device']

    def __init__(self, data=None, queryset=None, *, request=None, prefix=None):
        super().__init__(
            data=data, queryset=queryset, request=request, prefix=prefix)
        self.filters['device'].field.widget.attrs.update(
            {'class': 'netbox-select2-static form-control'})

    def filter_device(self, queryset, name, value):
        return queryset.filter(
            Q(interface__device__name__icontains=value)
        ).order_by('interface__id').distinct('interface__id')

    def search(self, queryset, name, value):
        if not value.strip():
            return queryset
        return queryset.filter(
            Q(interface__device__name__icontains=value) |
            Q(interface__name__icontains=value)
        ).order_by('interface__id').distinct('interface__id')
