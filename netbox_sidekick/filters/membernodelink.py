import django_filters

from django.db.models import Q

from netbox_sidekick.models import MemberNodeLinkType, MemberNodeLink


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
