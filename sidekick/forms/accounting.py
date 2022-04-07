from netbox.forms import NetBoxModelForm
from sidekick.models import (
    AccountingProfile,
    AccountingSource,
    BandwidthProfile,
)


class AccountingProfileForm(NetBoxModelForm):
    class Meta:
        model = AccountingProfile
        fields = ('member', 'name', 'enabled', 'comments', 'accounting_sources')


class AccountingSourceForm(NetBoxModelForm):
    class Meta:
        model = AccountingSource
        fields = ('device', 'name', 'destination',)


class BandwidthProfileForm(NetBoxModelForm):
    class Meta:
        model = BandwidthProfile
        fields = ('accounting_profile', 'effective_date', 'comments', 'traffic_cap', 'burst_limit',)
