from rest_framework.serializers import ModelSerializer, StringRelatedField
from netbox_sidekick.models import NIC


class NICSerializer(ModelSerializer):
    interface = StringRelatedField()

    class Meta:
        model = NIC
        fields = (
            'interface',
            'is_up', 'is_enabled',
            'tx_octets', 'rx_octets', 'tx_unicast_packets', 'rx_unicast_packets',
            'tx_multicast_packets', 'rx_multicast_packets',
            'tx_broadcast_packets', 'rx_broadcast_packets',
            'tx_discards', 'rx_discards',
            'tx_errors', 'rx_errors',
        )
