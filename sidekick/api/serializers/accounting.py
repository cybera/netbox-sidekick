from netbox.api.serializers import NetBoxModelSerializer
from rest_framework import serializers

from sidekick.models import (
    AccountingProfile,
    AccountingSource,
    BandwidthProfile,
)


class AccountingProfileSerializer(NetBoxModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='plugins-api:sidekick-api:accountingprofile-detail')

    class Meta:
        model = AccountingProfile
        fields = ('id', 'url', 'member', 'accounting_sources', 'name', 'enabled', 'comments',)


class AccountingSourceSerializer(NetBoxModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='plugins-api:sidekick-api:accountingsource-detail')

    class Meta:
        model = AccountingSource
        fields = ('id', 'url', 'device', 'name', 'destination',)


class BandwidthProfileSerializer(NetBoxModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='plugins-api:sidekick-api:bandwidthprofile-detail')

    class Meta:
        model = BandwidthProfile
        fields = ('id', 'url', 'effective_date', 'comments', 'traffic_cap', 'burst_limit',)
