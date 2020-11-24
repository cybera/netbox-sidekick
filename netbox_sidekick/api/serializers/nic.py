from rest_framework.serializers import ModelSerializer, StringRelatedField
from netbox_sidekick.models import NIC


class NICSerializer(ModelSerializer):
    interface = StringRelatedField()

    class Meta:
        model = NIC
        fields = (
            'interface',
            'admin_status', 'oper_status',
            'out_octets', 'in_octets',
            'out_unicast_packets', 'in_unicast_packets',
            'out_nunicast_packets', 'in_nunicast_packets',
            'out_errors', 'in_errors',
        )
