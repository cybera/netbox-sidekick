from django.db import models
from django.urls import reverse

from ipam.fields import IPAddressField

from utilities.models import ChangeLoggedModel


# LogicalSystem represents a logical system in a network device.
class LogicalSystem(ChangeLoggedModel):
    name = models.CharField(
        max_length=50,
        unique=True,
        verbose_name='Name',
        help_text='The name of the logical service',
    )

    slug = models.SlugField(
        unique=True,
    )

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('plugins:netbox_sidekick:logicalsystem_detail', args=[self.slug])


# RoutingType represents the routing type for a network service.
class RoutingType(ChangeLoggedModel):
    name = models.CharField(
        max_length=50,
        unique=True,
        verbose_name='Name',
        help_text='The name of the routing type',
    )

    slug = models.SlugField(
        unique=True,
    )

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('plugins:netbox_sidekick:routingtype_detail', args=[self.slug])


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
        'netbox_sidekick.Member',
        on_delete=models.PROTECT,
    )

    description = models.TextField(
        verbose_name='Description',
        help_text='A description of the service',
        blank=True,
    )

    comments = models.TextField(
        verbose_name='Comments',
        help_text='Additional comments about the service',
        blank=True,
    )

    active = models.BooleanField(
        verbose_name='Active',
        help_text='The active/inactive status of the service',
        default=True,
    )

    device = models.ForeignKey(
        to='dcim.Device',
        on_delete=models.PROTECT,
        related_name='network_services',
        null=True,
        blank=True,
    )

    interface = models.ForeignKey(
        to='dcim.Interface',
        on_delete=models.PROTECT,
        related_name='network_services',
        null=True,
        blank=True,
    )

    logical_system = models.ForeignKey(
        to='netbox_sidekick.LogicalSystem',
        on_delete=models.PROTECT,
        related_name='network_services',
        null=True,
        blank=True,
    )

    routing_type = models.ForeignKey(
        to='netbox_sidekick.RoutingType',
        on_delete=models.PROTECT,
        related_name='network_services',
        null=True,
        blank=True,
    )

    asn = models.CharField(
        max_length=255,
        verbose_name='ASN',
        help_text="The AS Number of the Member's service",
        blank=True,
        default='',
    )

    ipv4_unicast = models.BooleanField(
        verbose_name='IPv4 Unicast',
        help_text='Does the service support IPv4 Unicast?',
        default=True,
    )

    ipv4_multicast = models.BooleanField(
        verbose_name='IPv4 Multicast',
        help_text='Does the service support IPv4 Multicast?',
        default=True,
    )

    provider_router_address_ipv4 = IPAddressField(
        verbose_name='Provider IPv4 Router Address',
        help_text='IPv4 address of the Provider',
        null=True,
        blank=True,
    )

    member_router_address_ipv4 = IPAddressField(
        verbose_name='Member IPv4 Router Address',
        help_text='IPv4 address of the Member',
        null=True,
        blank=True,
    )

    ipv6_unicast = models.BooleanField(
        verbose_name='IPv6 Unicast',
        help_text='Does the service support IPv6 Unicast?',
        default=False,
    )

    ipv6_multicast = models.BooleanField(
        verbose_name='IPv6 Multicast',
        help_text='Does the service support IPv6 Multicast?',
        default=False,
    )

    provider_router_address_ipv6 = IPAddressField(
        verbose_name='Provider IPv6 Router Address',
        help_text='IPv6 address of the Provider',
        null=True,
        blank=True,
    )

    member_router_address_ipv6 = IPAddressField(
        verbose_name='Member IPv6 Router Address',
        help_text='IPv6 address of the Member',
        null=True,
        blank=True,
    )

    class Meta:
        ordering = ['member', 'network_service_type']

    def __str__(self):
        return f"{self.tenant.description}: {self.network_service_type}"

    def get_absolute_url(self):
        return reverse('plugins:netbox_sidekick:networkservice_detail', args=[self.pk])
