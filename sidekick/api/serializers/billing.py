from netbox.api.serializers import NetBoxModelSerializer
from rest_framework import serializers
from tenancy.api.serializers import TenantSerializer

from sidekick.models import TransitRate


class TransitRateSerializer(NetBoxModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='plugins-api:sidekick-api:transitrate-detail')
    tenant = TenantSerializer(nested=True, required=False, allow_null=True)

    class Meta:
        model = TransitRate
        fields = (
            'id', 'url', 'display', 'tenant', 'rate_per_mbit', 'effective_date', 'comments',)
        # `tenant` is absent from brief_fields on purpose: a nested TenantSerializer
        # for all 155 members is heavier than the rate row itself, and a caller
        # filling in billing wants the member name from the list they already have.
        brief_fields = ('id', 'url', 'display', 'rate_per_mbit', 'effective_date')
