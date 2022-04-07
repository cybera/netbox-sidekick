import django_filters
from netbox.filtersets import NetBoxModelFilterSet
from netbox.forms import NetBoxModelFilterSetForm

from django.db.models import Q

from dcim.models import Device

from sidekick.models import (
    NIC
)


def devices(request):
    devices = NIC.objects.order_by('interface__device__name').distinct(
        'interface__device__name').values_list('interface__device__id', flat=True)
    return Device.objects.filter(pk__in=devices)


class NICFilterSet(NetBoxModelFilterSet):
    device = django_filters.ModelChoiceFilter(
        label='Device',
        field_name='device',
        method='filter_device',
        queryset=devices,
    )

    class Meta:
        model = NIC
        fields = ('device',)

    def filter_device(self, queryset, name, value):
        return queryset.filter(
            Q(interface__device__name__icontains=value)
        ).order_by('interface__id').distinct('interface__id')


class NICFilterSetForm(NetBoxModelFilterSetForm):
    model = NIC
