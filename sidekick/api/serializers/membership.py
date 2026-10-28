from rest_framework import serializers
from tenancy.api.serializers import TenantSerializer
from users.api.serializers import UserSerializer

from netbox.api.serializers import NetBoxModelSerializer

from sidekick.models import MemberTenant


class MemberTenantSerializer(NetBoxModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name='plugins-api:sidekick-api:membertenant-detail')
    user = UserSerializer(nested=True)
    tenant = TenantSerializer(nested=True)

    class Meta:
        model = MemberTenant
        fields = ('id', 'url', 'display', 'user', 'tenant', 'role', 'note', 'created', 'last_updated')
        brief_fields = ('id', 'url', 'display', 'role')
