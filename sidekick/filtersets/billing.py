import django_filters

from django.db.models import Q

from netbox.filtersets import NetBoxModelFilterSet
from netbox.forms import NetBoxModelFilterSetForm

from tenancy.models import Tenant
from utilities.forms.fields import DynamicModelMultipleChoiceField

from sidekick.models import TransitRate


class TransitRateFilterSet(NetBoxModelFilterSet):
    tenant_id = django_filters.ModelMultipleChoiceFilter(
        field_name='tenant',
        queryset=Tenant.objects.filter(group__name='Members'),
        label='Member (ID)',
    )

    class Meta:
        model = TransitRate
        fields = ('tenant', 'rate_per_mbit', 'effective_date')

    def search(self, queryset, name, value):
        if not value.strip():
            return queryset
        return queryset.filter(
            Q(tenant__name__icontains=value) |
            Q(comments__icontains=value)
        )


class TransitRateFilterSetForm(NetBoxModelFilterSetForm):
    model = TransitRate

    tenant = DynamicModelMultipleChoiceField(
        queryset=Tenant.objects.filter(group__name='Members'),
        required=False,
        label='Member',
    )
