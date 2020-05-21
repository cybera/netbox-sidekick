from rest_framework.serializers import ModelSerializer, StringRelatedField
from netbox_sidekick.models import Member


class MemberSerializer(ModelSerializer):
    tenant = StringRelatedField()
    member_type = StringRelatedField()

    class Meta:
        model = Member
        fields = (
            'tenant',
            'member_type', 'active', 'billing_exempt', 'start_date', 'invoice_period_start',
            'number_of_users', 'billing_address_1', 'billing_address_2', 'billing_city',
            'billing_postal_code', 'billing_province', 'billing_country', 'url',
            'latitude', 'longitude',
        )
