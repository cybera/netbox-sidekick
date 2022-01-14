from django.db import models
from django.urls import reverse

from netbox.models import ChangeLoggedModel


# NIC represents a Network Card / Interface of a device.
#
# This model acts as an extension to a NetBox Interface.
class NIC(ChangeLoggedModel):
    interface = models.ForeignKey(
        to='dcim.Interface',
        on_delete=models.PROTECT,
        verbose_name='NIC',
        related_name='nic',
    )

    admin_status = models.IntegerField(
        verbose_name='Admin Status',
        help_text='Admin status of the interface',
        default=True,
    )

    oper_status = models.IntegerField(
        verbose_name='Oper Status',
        help_text='Oper status of the interface',
        default=True,
    )

    out_rate = models.BigIntegerField(
        verbose_name="Out Rate",
        help_text="Out Rate",
        default=0,
    )

    in_rate = models.BigIntegerField(
        verbose_name="In Rate",
        help_text="In Rate",
        default=0,
    )

    out_octets = models.BigIntegerField(
        verbose_name="Out Octets",
        help_text="Out Octets",
        default=0,
    )

    in_octets = models.BigIntegerField(
        verbose_name="In Octets",
        help_text="In Octets",
        default=0,
    )

    out_unicast_packets = models.BigIntegerField(
        verbose_name="Out Unicast Packets",
        help_text="Out Unicast Packets",
        default=0,
    )

    in_unicast_packets = models.BigIntegerField(
        verbose_name="In Unicast Packets",
        help_text="In Unicast Packets",
        default=0,
    )

    out_nunicast_packets = models.BigIntegerField(
        verbose_name="Out Non Unicast Packets",
        help_text="Out Non Unicast Packets",
        default=0,
    )

    in_nunicast_packets = models.BigIntegerField(
        verbose_name="In Non Unicast Packets",
        help_text="In Non Unicast Packets",
        default=0,
    )

    out_errors = models.BigIntegerField(
        verbose_name="Out Errors",
        help_text="Out Errors",
        default=0,
    )

    in_errors = models.BigIntegerField(
        verbose_name="In Errors",
        help_text="In Errors",
        default=0,
    )

    class Meta:
        ordering = ['interface__device__name', 'interface__name']
        verbose_name = 'NIC'
        verbose_name_plural = 'NICs'

    def __str__(self):
        return f"{self.interface.device.name} {self.interface.name}"

    def get_absolute_url(self):
        return reverse('plugins:sidekick:nic_detail', args=[self.interface.id])

    def graphite_device_name(self):
        return self.interface.device.name.lower().replace(' ', '_')

    def graphite_interface_name(self):
        return self.interface.name.lower().replace('/', '-').replace('.', '_')

    # If there are more than 5 entries for a NIC,
    # delete older ones.
    def save(self, *args, **kwargs):
        previous_entries = NIC.objects.filter(
            interface_id=self.interface_id).order_by('-last_updated')
        for entry in previous_entries[4:]:
            entry.delete()

        super().save(*args, **kwargs)
