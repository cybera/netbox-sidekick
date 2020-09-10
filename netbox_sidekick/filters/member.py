import django_filters

from django.db.models import Q

from netbox_sidekick.models import MemberType, Member


class MemberTypeFilterSet(django_filters.FilterSet):
    q = django_filters.CharFilter(
        method='search',
        label='Search',
    )

    class Meta:
        model = MemberType
        fields = []

    def search(self, queryset, name, value):
        if not value.strip():
            return queryset
        return queryset.filter(
            Q(name__icontains=value)
        ).distinct()


class MemberFilterSet(django_filters.FilterSet):
    q = django_filters.CharFilter(
        method='search',
        label='Search',
    )

    class Meta:
        model = Member
        fields = ['member_type']

    def __init__(self, data=None, queryset=None, *, request=None, prefix=None):
        super().__init__(
            data=data, queryset=queryset, request=request, prefix=prefix)
        self.filters['member_type'].field.widget.attrs.update(
            {'class': 'netbox-select2-static'})

    def search(self, queryset, name, value):
        if not value.strip():
            return queryset
        return queryset.filter(
            Q(tenant__description__icontains=value) |
            Q(invoice_period_start__icontains=value) |
            Q(billing_address_1__icontains=value) |
            Q(billing_address_2__icontains=value) |
            Q(billing_city__icontains=value) |
            Q(billing_postal_code__icontains=value) |
            Q(billing_province__icontains=value) |
            Q(billing_country__icontains=value) |
            Q(comments__icontains=value)
        ).distinct()
