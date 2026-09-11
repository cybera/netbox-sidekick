from rest_framework.serializers import ModelSerializer, SerializerMethodField, StringRelatedField
from sidekick.models import NIC


class NICSerializer(ModelSerializer):
    interface = StringRelatedField()
    interface_name = SerializerMethodField()
    description = SerializerMethodField()

    # The 'interface' field renders via Interface.__str__ (e.g.
    # 'xe-0/0/3:2.10 (MISSING)'), which is awkward to parse. Expose the
    # raw interface name so consumers (e.g. Sensu check scripts using
    # the bulk per-device endpoint) can match interfaces locally.
    def get_interface_name(self, obj):
        return obj.interface.name

    def get_description(self, obj):
        return obj.interface.description

    class Meta:
        model = NIC
        fields = (
            'interface',
            'interface_name',
            'description',
            'last_updated',
            'admin_status', 'oper_status',
            'out_octets', 'in_octets',
            'out_unicast_packets', 'in_unicast_packets',
            'out_nunicast_packets', 'in_nunicast_packets',
            'out_errors', 'in_errors',
            'out_rate', 'in_rate',
        )
