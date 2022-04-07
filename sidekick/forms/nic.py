from netbox.forms import NetBoxModelForm
from sidekick.models import (
    NIC
)


class NICForm(NetBoxModelForm):
    class Meta:
        model = NIC
        fields = ('interface', 'admin_status', 'oper_status',
                  'out_rate', 'in_rate',
                  'out_octets', 'in_octets',
                  'out_unicast_packets', 'in_unicast_packets',
                  'out_nunicast_packets', 'in_nunicast_packets',
                  'out_errors', 'in_errors',)
