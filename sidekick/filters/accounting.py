from netbox.filtersets import NetBoxModelFilterSet
from netbox.forms import NetBoxModelFilterSetForm

from dcim.models import Device
from tenancy.models import Tenant
from utilities.forms import DynamicModelMultipleChoiceField

from sidekick.models import (
    AccountingProfile,
    AccountingSource,
    BandwidthProfile,
)


class AccountingProfileFilterSet(NetBoxModelFilterSet):
    class Meta:
        model = AccountingProfile
        fields = ('member', 'enabled')


class AccountingProfileFilterSetForm(NetBoxModelFilterSetForm):
    model = AccountingProfile

    member = DynamicModelMultipleChoiceField(
        queryset=Tenant.objects.filter(group__name='Members'),
        required=False,
        label='Member',
    )


class AccountingSourceFilterSet(NetBoxModelFilterSet):
    class Meta:
        model = AccountingSource
        fields = ('device',)


class AccountingSourceFilterSetForm(NetBoxModelFilterSetForm):
    model = AccountingSource

    device = DynamicModelMultipleChoiceField(
        queryset=Device.objects.filter(name__icontains="router").distinct(),
        required=False,
        label='Device',
    )


class BandwidthProfileFilterSet(NetBoxModelFilterSet):
    class Meta:
        model = BandwidthProfile
        fields = ('accounting_profile__member',)


class BandwidthProfileFilterSetForm(NetBoxModelFilterSetForm):
    model = BandwidthProfile

    member = DynamicModelMultipleChoiceField(
        queryset=Tenant.objects.filter(group__name='Members'),
        required=False,
        label='Member',
    )
