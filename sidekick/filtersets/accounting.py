import django_filters

from django.db.models import Q

from netbox.filtersets import NetBoxModelFilterSet
from netbox.forms import NetBoxModelFilterSetForm

from dcim.models import Device
from tenancy.models import Tenant
from utilities.forms.fields import DynamicModelMultipleChoiceField

from sidekick.models import (
    AccountingProfile,
    AccountingSource,
    BandwidthProfile,
)


class AccountingProfileFilterSet(NetBoxModelFilterSet):
    member_id = django_filters.ModelMultipleChoiceFilter(
        field_name='member',
        queryset=Tenant.objects.filter(group__name='Members'),
        label='Member (ID)',
    )

    class Meta:
        model = AccountingProfile
        fields = ('member', 'enabled')

    def search(self, queryset, name, value):
        if not value.strip():
            return queryset
        return queryset.filter(
            Q(name__icontains=value) |
            Q(member__name__icontains=value)
        )


class AccountingProfileFilterSetForm(NetBoxModelFilterSetForm):
    model = AccountingProfile

    member = DynamicModelMultipleChoiceField(
        queryset=Tenant.objects.filter(group__name='Members'),
        required=False,
        label='Member',
    )


class AccountingSourceFilterSet(NetBoxModelFilterSet):
    device_id = django_filters.ModelMultipleChoiceFilter(
        field_name='device',
        queryset=Device.objects.all(),
        label='Device (ID)',
    )

    class Meta:
        model = AccountingSource
        fields = ('device',)

    def search(self, queryset, name, value):
        if not value.strip():
            return queryset
        return queryset.filter(
            Q(name__icontains=value) |
            Q(destination__icontains=value) |
            Q(device__name__icontains=value)
        )


class AccountingSourceFilterSetForm(NetBoxModelFilterSetForm):
    model = AccountingSource

    device = DynamicModelMultipleChoiceField(
        queryset=Device.objects.filter(name__icontains="router").distinct(),
        required=False,
        label='Device',
    )


class BandwidthProfileFilterSet(NetBoxModelFilterSet):
    accounting_profile_id = django_filters.ModelMultipleChoiceFilter(
        field_name='accounting_profile',
        queryset=AccountingProfile.objects.all(),
        label='Accounting profile (ID)',
    )

    class Meta:
        model = BandwidthProfile
        fields = ('accounting_profile__member', 'accounting_profile')

    def search(self, queryset, name, value):
        if not value.strip():
            return queryset
        return queryset.filter(
            Q(accounting_profile__name__icontains=value) |
            Q(accounting_profile__member__name__icontains=value)
        )


class BandwidthProfileFilterSetForm(NetBoxModelFilterSetForm):
    model = BandwidthProfile

    member = DynamicModelMultipleChoiceField(
        queryset=Tenant.objects.filter(group__name='Members'),
        required=False,
        label='Member',
    )
