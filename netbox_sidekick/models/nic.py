from django.db import models
from django.urls import reverse

from utilities.models import ChangeLoggedModel


# NIC represents a Network Card / Interface of a device.
#
# This model acts as an extension to a NetBox Interface.
class NIC(ChangeLoggedModel):
    interface = models.OneToOneField(
        'dcim.Interface',
        on_delete=models.PROTECT,
    )

    is_up = models.BooleanField(
        verbose_name='Is Up?',
        help_text='Is the interface up?',
        default=True,
    )

    is_enabled = models.BooleanField(
        verbose_name='Is Enabled?',
        help_text='Is the interface administratively enabled?',
        default=True,
    )

    tx_octets = models.BigIntegerField(
        verbose_name="TX Octets",
        help_text="TX Octets",
        default=0,
    )

    rx_octets = models.BigIntegerField(
        verbose_name="RX Octets",
        help_text="RX Octets",
        default=0,
    )

    tx_unicast_packets = models.BigIntegerField(
        verbose_name="TX Unicast Packets",
        help_text="TX Unicast Packets",
        default=0,
    )

    rx_unicast_packets = models.BigIntegerField(
        verbose_name="RX Unicast Packets",
        help_text="RX Unicast Packets",
        default=0,
    )

    tx_multicast_packets = models.BigIntegerField(
        verbose_name="TX Multicast Packets",
        help_text="TX Multicast Packets",
        default=0,
    )

    rx_multicast_packets = models.BigIntegerField(
        verbose_name="RX Multicast Packets",
        help_text="RX Multicast Packets",
        default=0,
    )

    tx_broadcast_packets = models.BigIntegerField(
        verbose_name="TX Broadcast Packets",
        help_text="TX Broadcast Packets",
        default=0,
    )

    rx_broadcast_packets = models.BigIntegerField(
        verbose_name="RX Broadcast Packets",
        help_text="RX Broadcast Packets",
        default=0,
    )

    tx_discards = models.BigIntegerField(
        verbose_name="TX Discards",
        help_text="TX Discards",
        default=0,
    )

    rx_discards = models.BigIntegerField(
        verbose_name="RX Discards",
        help_text="RX Discards",
        default=0,
    )

    tx_errors = models.BigIntegerField(
        verbose_name="TX Errors",
        help_text="TX Errors",
        default=0,
    )

    rx_errors = models.BigIntegerField(
        verbose_name="RX Errors",
        help_text="RX Errors",
        default=0,
    )

    class Meta:
        ordering = ['interface']

    def __str__(self):
        return self.interface.name

    def get_absolute_url(self):
        return reverse('plugins:netbox_sidekick:interface_detail', args=[self.pk])
