import django_filters

from django.db.models import Q

from netbox_sidekick.models import MemberNodeType, MemberNode


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
        super().__init__(
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
