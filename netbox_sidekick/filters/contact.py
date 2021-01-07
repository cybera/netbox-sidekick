import django_filters

from django.db.models import Q

from tenancy.models import Tenant
from netbox_sidekick.models import ContactType, Contact


class ContactTypeFilterSet(django_filters.FilterSet):
    q = django_filters.CharFilter(
        method='search',
        label='Search',
    )

    class Meta:
        model = ContactType
        fields = []

    def search(self, queryset, name, value):
        if not value.strip():
            return queryset
        return queryset.filter(
            Q(name__icontains=value)
        ).distinct()


class ContactFilterSet(django_filters.FilterSet):
    q = django_filters.CharFilter(
        method='search',
        label='Search',
    )

    member = django_filters.ModelChoiceFilter(
        label='Member',
        field_name='member',
        method='filter_member',
        queryset=Tenant.objects.filter(
            group__name='Members')
    )

    class Meta:
        model = Contact
        fields = ['member']

    def __init__(self, data=None, queryset=None, *, request=None, prefix=None):
        super().__init__(
            data=data, queryset=queryset, request=request, prefix=prefix)
        self.filters['member'].field.widget.attrs.update(
            {'class': 'netbox-select2-static'})

    def filter_member(self, queryset, name, value):
        return queryset.filter(
            Q(membercontact__member__name__icontains=value) |
            Q(membercontact__member__description__icontains=value)
        ).distinct()

    def search(self, queryset, name, value):
        if not value.strip():
            return queryset
        return queryset.filter(
            Q(first_name__icontains=value) |
            Q(last_name__icontains=value) |
            Q(title__icontains=value) |
            Q(email__icontains=value) |
            Q(phone__icontains=value) |
            Q(comments__icontains=value)
        ).distinct()
