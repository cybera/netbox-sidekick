import django_filters

from django.db.models import Q

from .models import (
    MemberType, Member,
    MemberNodeType, MemberNode,
    MemberNodeLinkType, MemberNodeLink,
    NetworkServiceType, NetworkService
)


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
        super(MemberFilterSet, self).__init__(
            data=data, queryset=queryset, request=request, prefix=prefix)
        self.filters['member_type'].field.widget.attrs.update(
            {'class': 'netbox-select2-static'})

    def search(self, queryset, name, value):
        if not value.strip():
            return queryset
        return queryset.filter(
            Q(tenant__icontains=value) |
            Q(invoice_period_start__icontains=value) |
            Q(billing_contact_first_name__icontains=value) |
            Q(billing_contact_last_name__icontains=value) |
            Q(billing_contact_title__icontains=value) |
            Q(billing_contact_phone_number__icontains=value) |
            Q(billing_contact_email_address__icontains=value) |
            Q(billing_contact_address_1__icontains=value) |
            Q(billing_contact_address_2__icontains=value) |
            Q(billing_contact_city__icontains=value) |
            Q(billing_contact_postal_code__icontains=value) |
            Q(billing_contact_province__icontains=value) |
            Q(billing_contact_country__icontains=value) |
            Q(technical_contact_first_name__icontains=value) |
            Q(technical_contact_last_name__icontains=value) |
            Q(technical_contact_title__icontains=value) |
            Q(technical_contact_phone_number__icontains=value) |
            Q(technical_contact_email_address__icontains=value) |
            Q(comments__icontains=value)
        ).distinct()


class MemberNodeTypeFilterSet(django_filters.FilterSet):
    q = django_filters.CharFilter(
        method='search',
        label='Search',
    )

    class Meta:
        model = MemberNodeType
        fields = []

    def search(self, queryset, name, value):
        if not value.strip():
            return queryset
        return queryset.filter(
            Q(name__icontains=value)
        ).distinct()


class MemberNodeFilterSet(django_filters.FilterSet):
    q = django_filters.CharFilter(
        method='search',
        label='Search',
    )

    class Meta:
        model = MemberNode
        fields = ['owner', 'node_type']

    def __init__(self, data=None, queryset=None, *, request=None, prefix=None):
        super(MemberNodeFilterSet, self).__init__(
            data=data, queryset=queryset, request=request, prefix=prefix)
        self.filters['owner'].field.widget.attrs.update(
            {'class': 'netbox-select2-static'})
        self.filters['node_type'].field.widget.attrs.update(
            {'class': 'netbox-select2-static'})

    def search(self, queryset, name, value):
        if not value.strip():
            return queryset
        return queryset.filter(
            Q(name__icontains=value) |
            Q(label__icontains=value) |
            Q(internal_id__icontains=value) |
            Q(address__icontains=value)
        ).distinct()


class MemberNodeLinkTypeFilterSet(django_filters.FilterSet):
    q = django_filters.CharFilter(
        method='search',
        label='Search',
    )

    class Meta:
        model = MemberNodeLinkType
        fields = []

    def search(self, queryset, name, value):
        if not value.strip():
            return queryset
        return queryset.filter(
            Q(name__icontains=value)
        ).distinct()


class MemberNodeLinkFilterSet(django_filters.FilterSet):
    q = django_filters.CharFilter(
        method='search',
        label='Search',
    )

    class Meta:
        model = MemberNodeLink
        fields = ['owner', 'link_type', 'a_endpoint', 'z_endpoint']

    def __init__(self, data=None, queryset=None, *, request=None, prefix=None):
        super(MemberNodeLinkFilterSet, self).__init__(
            data=data, queryset=queryset, request=request, prefix=prefix)
        self.filters['owner'].field.widget.attrs.update(
            {'class': 'netbox-select2-static'})
        self.filters['link_type'].field.widget.attrs.update(
            {'class': 'netbox-select2-static'})
        self.filters['a_endpoint'].field.widget.attrs.update(
            {'class': 'netbox-select2-static'})
        self.filters['z_endpoint'].field.widget.attrs.update(
            {'class': 'netbox-select2-static'})

    def search(self, queryset, name, value):
        if not value.strip():
            return queryset
        return queryset.filter(
            Q(name__icontains=value) |
            Q(label__icontains=value) |
            Q(internal_id__icontains=value) |
            Q(throughput__icontains=value)
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
        fields = ['member', 'network_service_type']

    def __init__(self, data=None, queryset=None, *, request=None, prefix=None):
        super(NetworkServiceFilterSet, self).__init__(
            data=data, queryset=queryset, request=request, prefix=prefix)
        self.filters['member'].field.widget.attrs.update(
            {'class': 'netbox-select2-static'})
        self.filters['network_service_type'].field.widget.attrs.update(
            {'class': 'netbox-select2-static'})

    def search(self, queryset, name, value):
        if not value.strip():
            return queryset
        return queryset.filter(
            Q(name__icontains=value) |
            Q(comments__icontains=value)
        ).distinct()
