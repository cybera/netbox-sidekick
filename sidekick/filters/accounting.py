import django_filters

from django.db.models import Q

from sidekick.models import (
    AccountingProfile,
    AccountingClass,
    BandwidthProfile,
)


class AccountingProfileFilterSet(django_filters.FilterSet):
    q = django_filters.CharFilter(
        method='search',
        label='Search',
    )

    class Meta:
        model = AccountingProfile
        fields = ['member', 'enabled']

    def __init__(self, data=None, queryset=None, *, request=None, prefix=None):
        super().__init__(
            data=data, queryset=queryset, request=request, prefix=prefix)
        self.filters['member'].field.widget.attrs.update(
            {'class': 'netbox-select2-static form-control'})
        self.filters['enabled'].field.widget.attrs.update(
            {'class': 'netbox-select2-static form-control'})

    def search(self, queryset, name, value):
        if not value.strip():
            return queryset
        return queryset.filter(
            Q(name__icontains=value) |
            Q(comments__icontains=value)
        ).distinct()

    @property
    def qs(self):
        parent = super().qs
        enabled = self.request.GET.get('enabled', 'true')
        if enabled.lower() == 'false':
            enabled = False
        else:
            enabled = True
        return parent.filter(enabled=enabled)


class AccountingClassFilterSet(django_filters.FilterSet):
    q = django_filters.CharFilter(
        method='search',
        label='Search',
    )

    class Meta:
        model = AccountingClass
        fields = ['device']

    def __init__(self, data=None, queryset=None, *, request=None, prefix=None):
        super().__init__(
            data=data, queryset=queryset, request=request, prefix=prefix)
        self.filters['device'].field.widget.attrs.update(
            {'class': 'netbox-select2-static form-control'})

    def search(self, queryset, name, value):
        if not value.strip():
            return queryset
        return queryset.filter(
            Q(name__icontains=value) |
            Q(destination__icontains=value)
        ).distinct()


class BandwidthProfileFilterSet(django_filters.FilterSet):
    q = django_filters.CharFilter(
        method='search',
        label='Search',
    )

    class Meta:
        model = BandwidthProfile
        fields = ['accounting_profile__member']

    def __init__(self, data=None, queryset=None, *, request=None, prefix=None):
        super().__init__(
            data=data, queryset=queryset, request=request, prefix=prefix)
        self.filters['accounting_profile__member'].field.widget.attrs.update(
            {'class': 'netbox-select2-static form-control'})

    def search(self, queryset, name, value):
        if not value.strip():
            return queryset
        return queryset.filter(
            Q(accounting_profile__name__icontains=value) |
            Q(accounting_profile__comments__icontains=value) |
            Q(comments__icontains=value)
        ).distinct()
