from netbox.api.serializers import NetBoxModelSerializer
from rest_framework import serializers

from sidekick.models import (
    AccountingSource,
)


class AccountingSourceSerializer(NetBoxModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='plugins-api:sidekick-api:accountingsource-detail')

    class Meta:
        model = AccountingSource
        fields = ('id', 'url', 'device', 'name', 'destination',)
