from django.db import models
from django.urls import reverse

from utilities.models import ChangeLoggedModel


# NetworkServiceType is a Type of Network Service provided to members.
# For example: Peering, Transit, Virtual Firewall.
# The name NetworkService is used because "Service"
# is already a core NetBox model.
class NetworkServiceType(ChangeLoggedModel):
    name = models.CharField(
        max_length=50,
        unique=True,
        verbose_name='Name',
        help_text='The name of the network service type',
    )

    slug = models.SlugField(
        unique=True,
    )

    description = models.CharField(
        max_length=255,
        verbose_name='Description',
        help_text='A description of the Network Service Type',
        blank=True,
        default='',
    )

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('plugins:netbox_sidekick:networkservicetype_detail', args=[self.slug])


class NetworkService(ChangeLoggedModel):
    name = models.CharField(
        max_length=255,
        verbose_name='Name',
        help_text='A descriptive name for the service',
    )

    network_service_type = models.ForeignKey(
        to='netbox_sidekick.NetworkServiceType',
        on_delete=models.PROTECT,
        verbose_name='Service Type',
        related_name='network_service',
    )

    member = models.ForeignKey(
        'Member',
        on_delete=models.PROTECT,
    )

    comments = models.TextField(
        blank=True,
    )

    asn = models.CharField(
        max_length=255,
        verbose_name='ASN',
        help_text="The AS Number of the Member's service",
        blank=True,
        default='',
    )

    class Meta:
        ordering = ['member', 'network_service_type']

    def __str__(self):
        return f"{self.tenant.description}: {self.network_service_type}"

    def get_absolute_url(self):
        return reverse('plugins:netbox_sidekick:networkservice_detail', args=[self.pk])
