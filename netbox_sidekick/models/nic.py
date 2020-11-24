from django.db import models
from django.urls import reverse

from extras.models import ChangeLoggedModel


# NIC represents a Network Card / Interface of a device.
#
# This model acts as an extension to a NetBox Interface.
class NIC(ChangeLoggedModel):
    interface = models.OneToOneField(
        'dcim.Interface',
        on_delete=models.PROTECT,
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

    def __str__(self):
        return f"{self.interface.device.name} {self.interface.name}"

    def get_absolute_url(self):
        return reverse('plugins:netbox_sidekick:nic_detail', args=[self.pk])
