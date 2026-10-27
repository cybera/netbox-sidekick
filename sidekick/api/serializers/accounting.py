from netbox.api.serializers import NetBoxModelSerializer
from rest_framework import serializers

from sidekick.models import (
    AccountingProfile,
    AccountingSource,
    BandwidthProfile,
)

from dcim.api.serializers import DeviceSerializer
from tenancy.api.serializers import TenantSerializer


class AccountingProfileSerializer(NetBoxModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='plugins-api:sidekick-api:accountingprofile-detail')
    member = TenantSerializer(nested=True, required=False, allow_null=True)

    class Meta:
        model = AccountingProfile
        fields = ('id', 'url', 'display', 'member', 'accounting_sources', 'name', 'enabled', 'comments',)
        brief_fields = ('id', 'url', 'display', 'name', 'member')


class AccountingSourceSerializer(NetBoxModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='plugins-api:sidekick-api:accountingsource-detail')
    device = DeviceSerializer(nested=True, required=False, allow_null=True)

    class Meta:
        model = AccountingSource
        fields = ('id', 'url', 'display', 'device', 'name', 'destination',)
        brief_fields = ('id', 'url', 'display', 'name', 'destination')


class BandwidthProfileSerializer(NetBoxModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='plugins-api:sidekick-api:bandwidthprofile-detail')
    # Nested so one request answers "which member does this cap belong to": the brief
    # accounting profile carries `member`, so the chain
    # bandwidth profile -> accounting profile -> tenant resolves in a single response.
    # Before 2026-10-27 neither `accounting_profile` nor `billable` was published, and
    # a consumer could not tell whose cap a row was or whether it was billable.
    accounting_profile = AccountingProfileSerializer(nested=True, required=False, allow_null=True)

    class Meta:
        model = BandwidthProfile
        fields = (
            'id', 'url', 'display', 'accounting_profile', 'effective_date', 'comments',
            'traffic_cap', 'burst_limit', 'billable',)
        brief_fields = (
            'id', 'url', 'display', 'accounting_profile', 'effective_date', 'traffic_cap',
            'burst_limit', 'billable')
