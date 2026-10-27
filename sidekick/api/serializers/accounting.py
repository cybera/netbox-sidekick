from netbox.api.serializers import NetBoxModelSerializer
from rest_framework import serializers

from sidekick.models import (
    AccountingProfile,
    AccountingSource,
    BandwidthProfile,
)

from tenancy.api.serializers import TenantSerializer


class AccountingProfileSerializer(NetBoxModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='plugins-api:sidekick-api:accountingprofile-detail')
    member = TenantSerializer(nested=True, required=False, allow_null=True)

    class Meta:
        model = AccountingProfile
        fields = ('id', 'url', 'display', 'member', 'accounting_sources', 'name', 'enabled', 'comments',)
        brief_fields = ('id', 'url', 'display', 'name', 'enabled')


class AccountingSourceSerializer(NetBoxModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='plugins-api:sidekick-api:accountingsource-detail')

    class Meta:
        model = AccountingSource
        fields = ('id', 'url', 'display', 'device', 'name', 'destination',)
        brief_fields = ('id', 'url', 'display', 'name', 'destination')


class BandwidthProfileSerializer(NetBoxModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='plugins-api:sidekick-api:bandwidthprofile-detail')

    class Meta:
        model = BandwidthProfile
        fields = ('id', 'url', 'display', 'effective_date', 'comments', 'traffic_cap', 'burst_limit',)
        brief_fields = ('id', 'url', 'display', 'effective_date', 'traffic_cap', 'burst_limit')
