from django.db import models
from django.urls import reverse
from django.utils import timezone

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


# NetworkServiceConnectionType is a Type of Network Connection Service
# provided to members.
# For example: Upstream, SuperNet, DWDM.
class NetworkServiceConnectionType(ChangeLoggedModel):
    name = models.CharField(
        max_length=50,
        unique=True,
        verbose_name='Name',
        help_text='The name of the network service connection type',
    )

    slug = models.SlugField(
        unique=True,
    )

    description = models.CharField(
        max_length=255,
        verbose_name='Description',
        help_text='A description of the network service connection type',
        blank=True,
        default='',
    )

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('plugins:netbox_sidekick:networkserviceconnectiontype_detail', args=[self.slug])


# NetworkServiceConnection represents a network service connection
# that connects a member.
# A member can then be subscribed to one or more services that
# are related to a network service connection.
class NetworkServiceConnection(ChangeLoggedModel):
    name = models.CharField(
        max_length=255,
        verbose_name='Name',
        help_text='A descriptive name for the network service connection',
    )

    network_service_connection_type = models.ForeignKey(
        to='netbox_sidekick.NetworkServiceConnectionType',
        on_delete=models.PROTECT,
        verbose_name='Service Connection Type',
        related_name='network_service_connection',
    )

    member = models.ForeignKey(
        'netbox_sidekick.Member',
        on_delete=models.PROTECT,
    )

    start_date = models.DateField(
        verbose_name='Start Date',
        help_text='The date the service connection started',
        blank=True,
        default=timezone.now,
    )

    end_date = models.DateField(
        verbose_name='End Date',
        help_text='The date the service connection ended',
        blank=True,
        null=True,
    )

    description = models.TextField(
        verbose_name='Description',
        help_text='A description of the service connection',
        blank=True,
    )

    comments = models.TextField(
        verbose_name='Comments',
        help_text='Additional comments about the service connection',
        blank=True,
    )

    active = models.BooleanField(
        verbose_name='Active',
        help_text='The active/inactive status of the service connection',
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
        related_name='network_service_connections',
        null=True,
        blank=True,
    )

    routing_type = models.ForeignKey(
        to='netbox_sidekick.RoutingType',
        on_delete=models.PROTECT,
        related_name='network_service_connections',
        null=True,
        blank=True,
    )

    asn = models.CharField(
        max_length=255,
        verbose_name='ASN',
        help_text="The AS Number of the Member's service connection",
        blank=True,
        default='',
    )

    ipv4_unicast = models.BooleanField(
        verbose_name='IPv4 Unicast',
        help_text='Does the service connection support IPv4 Unicast?',
        default=True,
    )

    ipv4_multicast = models.BooleanField(
        verbose_name='IPv4 Multicast',
        help_text='Does the service connection support IPv4 Multicast?',
        default=True,
    )

    ipv4_prefixes = models.TextField(
        verbose_name='IPv4 Prefixes',
        help_text='IPv4 Prefixes of the member',
        null=True,
        blank=True,
    )

    provider_router_address_ipv4 = models.ForeignKey(
        to='ipam.IPAddress',
        on_delete=models.PROTECT,
        verbose_name='Provider IPv4 Router Address',
        related_name='provider_router_address_ipv4',
        null=True,
        blank=True,
    )

    member_router_address_ipv4 = models.ForeignKey(
        to='ipam.IPAddress',
        on_delete=models.PROTECT,
        verbose_name='Member IPv4 Router Address',
        related_name='member_router_address_ipv4',
        null=True,
        blank=True,
    )

    ipv6_unicast = models.BooleanField(
        verbose_name='IPv6 Unicast',
        help_text='Does the service connection support IPv6 Unicast?',
        default=False,
    )

    ipv6_multicast = models.BooleanField(
        verbose_name='IPv6 Multicast',
        help_text='Does the service connection support IPv6 Multicast?',
        default=False,
    )

    ipv6_prefixes = models.TextField(
        verbose_name='IPv6 Prefixes',
        help_text='IPv6 Prefixes of the member',
        null=True,
        blank=True,
    )

    provider_router_address_ipv6 = models.ForeignKey(
        to='ipam.IPAddress',
        on_delete=models.PROTECT,
        verbose_name='Provider IPv6 Router Address',
        related_name='provider_router_address_ipv6',
        null=True,
        blank=True,
    )

    member_router_address_ipv6 = models.ForeignKey(
        to='ipam.IPAddress',
        on_delete=models.PROTECT,
        verbose_name='Member IPv6 Router Address',
        related_name='member_router_address_ipv6',
        null=True,
        blank=True,
    )

    class Meta:
        ordering = ['member', 'network_service_connection_type']

    def __str__(self):
        return f"{self.tenant.description}: {self.name}"

    def get_absolute_url(self):
        return reverse('plugins:netbox_sidekick:networkserviceconnection_detail', args=[self.pk])
