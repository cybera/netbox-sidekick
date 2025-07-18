import netaddr

from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify

from dcim.models import Interface
from ipam.models import Prefix

from netbox.models import NetBoxModel


# LogicalSystem represents a logical system in a network device.
class LogicalSystem(NetBoxModel):
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
        verbose_name = 'Logical System'
        verbose_name_plural = 'Logical Systems'

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('plugins:sidekick:logicalsystem_detail', args=[self.pk])


# RoutingType represents the routing type for a network service.
class RoutingType(NetBoxModel):
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
        verbose_name = 'Routing Type'
        verbose_name_plural = 'Routing Types'

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('plugins:sidekick:routingtype_detail', args=[self.pk])


# NetworkServiceType is a Type of Network Service
# provided to members.
# For example: Upstream, SuperNet, DWDM.
class NetworkServiceType(NetBoxModel):
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
        help_text='A description of the network service type',
        blank=True,
        default='',
    )

    class Meta:
        ordering = ['name']
        verbose_name = 'Network Service Type'
        verbose_name_plural = 'Network Service Types'

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('plugins:sidekick:networkservicetype_detail', args=[self.pk])


# NetworkService represents a network service for of a member.
# A member can then be subscribed to one or more services that
# are related to a network service.
class NetworkService(NetBoxModel):
    name = models.CharField(
        max_length=255,
        verbose_name='Name',
        help_text='A descriptive name for the network service. Example: "Calgary - Primary"',
    )

    network_service_type = models.ForeignKey(
        to='sidekick.NetworkServiceType',
        on_delete=models.PROTECT,
        verbose_name='Service Type',
        related_name='network_service_type',
    )

    member = models.ForeignKey(
        'tenancy.Tenant',
        on_delete=models.PROTECT,
    )

    member_site = models.ForeignKey(
        'dcim.Site',
        verbose_name='Member Site',
        on_delete=models.PROTECT,
    )

    legacy_id = models.CharField(
        max_length=255,
        verbose_name='Old ID for migrations',
        help_text='The ID of the service in an old system',
        blank=True,
        default='',
    )

    start_date = models.DateField(
        verbose_name='Start Date',
        help_text='The date the service started',
        blank=True,
        null=True,
        default=timezone.now,
    )

    end_date = models.DateField(
        verbose_name='End Date',
        help_text='The date the service ended',
        blank=True,
        null=True,
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

    backup_for = models.ForeignKey(
        "self",
        on_delete=models.PROTECT,
        verbose_name="Backup Service for",
        help_text="The primary service",
        blank=True,
        null=True,
    )

    accounting_profile = models.ForeignKey(
        'sidekick.AccountingProfile',
        on_delete=models.PROTECT,
        verbose_name='Accounting Profile',
        help_text='The accounting profile applied to this service',
        blank=True,
        null=True,
    )

    class Meta:
        ordering = ['member', 'network_service_type']
        verbose_name = 'Network Service'
        verbose_name_plural = 'Network Services'

    def __str__(self):
        v = f"{self.member.name}: {self.name}"
        if not self.active:
            v = f"{v} (inactive)"

        return v

    def get_absolute_url(self):
        return reverse('plugins:sidekick:networkservice_detail', args=[self.pk])

    def graphite_service_name(self):
        member_name = slugify(self.member.name)
        service_name = slugify(self.name)
        return f"services.{member_name}.{service_name}"

    def get_prefixes(self, version=4):
        prefixes = []
        for network_device in self.network_service_devices.all():
            for l3 in network_device.network_service_l3.all():
                for prefix in l3.ip_prefixes.all():
                    if prefix.prefix.version == version:
                        prefixes.append(prefix.prefix)
        prefixes.sort()
        return prefixes

    # old - remove soon
    def get_ipv4_prefixes(self):
        prefixes = []
        for network_device in self.network_service_devices.all():
            for l3 in network_device.network_service_l3.all():
                for prefix in l3.ipv4_prefixes.split("\n"):
                    prefix = prefix.strip()
                    if prefix:
                        try:
                            prefix = netaddr.IPNetwork(prefix)
                        except netaddr.core.AddrFormatError:
                            continue
                        if prefix not in prefixes:
                            prefixes.append(prefix)
        prefixes.sort()
        return prefixes

    # old - remove soon
    def get_ipv6_prefixes(self):
        prefixes = []
        for network_device in self.network_service_devices.all():
            for l3 in network_device.network_service_l3.all():
                for prefix in l3.ipv6_prefixes.split("\n"):
                    prefix = prefix.strip()
                    if prefix:
                        try:
                            prefix = netaddr.IPNetwork(prefix)
                        except netaddr.core.AddrFormatError:
                            continue
                        prefixes.append(prefix)
        prefixes.sort()
        return prefixes

    # old - remove soon
    def get_ip_prefixes(self):
        prefixes = self.get_ipv4_prefixes()
        prefixes.extend(self.get_ipv6_prefixes())
        prefixes.sort()
        return prefixes

    def get_backup_service(self):
        return NetworkService.objects.filter(backup_for=self.id)


# NetworkServiceDevice represents a device that is part
# of a member's network service.
# One or more devices may compose a member's service.
class NetworkServiceDevice(NetBoxModel):
    network_service = models.ForeignKey(
        to='sidekick.NetworkService',
        on_delete=models.PROTECT,
        related_name='network_service_devices',
        null=True,
        blank=True,
    )

    device = models.ForeignKey(
        to='dcim.Device',
        on_delete=models.PROTECT,
        related_name='network_service_devices',
        null=True,
        blank=True,
    )

    interface = models.CharField(
        max_length=255,
        verbose_name='Interface',
        help_text='The interface of the service',
        blank=True,
        null=True,
    )

    vlan = models.IntegerField(
        verbose_name='VLAN of the service',
        help_text='VLAN of the service',
        null=True,
        blank=True,
    )

    comments = models.TextField(
        verbose_name='Comments',
        help_text='Additional comments about the service',
        blank=True,
    )

    legacy_id = models.CharField(
        max_length=255,
        verbose_name='Old ID for migrations',
        help_text='The ID of the service device in an old system',
        blank=True,
        default='',
    )

    class Meta:
        verbose_name = 'Network Service Device'
        verbose_name_plural = 'Network Service Devices'

    def __str__(self):
        return f"{self.network_service} on {self.device.name} {self.interface}"

    # def get_absolute_url(self):
    #     return reverse('plugins:sidekick:networkservicedevice_detail', args=[self.pk])

    def get_interface_entry(self):
        try:
            return Interface.objects.get(device=self.device, name=self.interface)
        except Interface.DoesNotExist:
            return None


# NetworkServiceL2 represents an L2 component of a member's
# network service. A network service may have one or more
# L2 components.
class NetworkServiceL2(NetBoxModel):
    network_service_device = models.ForeignKey(
        to='sidekick.NetworkServiceDevice',
        on_delete=models.PROTECT,
        related_name='network_service_l2',
        null=True,
        blank=True,
    )

    vlan = models.IntegerField(
        verbose_name='VLAN of the L2 service',
        help_text='VLAN of the L2 service',
        null=True,
        blank=True,
    )

    comments = models.TextField(
        verbose_name='Comments',
        help_text='Additional comments about the service',
        blank=True,
    )

    legacy_id = models.CharField(
        max_length=255,
        verbose_name='Old ID for migrations',
        help_text='The ID of the L2 service in an old system',
        blank=True,
        default='',
    )

    class Meta:
        verbose_name = "Network Service L2"
        verbose_name_plural = "Network Services L2"

    def __str__(self):
        return f"{self.network_service_device} L2 Service"

    # def get_absolute_url(self):
    #     return reverse('plugins:sidekick:networkservicel2_detail', args=[self.pk])


# NetworkServiceL3 represents an L3 component of a member's
# network service. A network service may have one or more
# L3 components.
class NetworkServiceL3(NetBoxModel):
    network_service_device = models.ForeignKey(
        to='sidekick.NetworkServiceDevice',
        on_delete=models.PROTECT,
        related_name='network_service_l3',
        null=True,
        blank=True,
    )

    member = models.ForeignKey(
        'tenancy.Tenant',
        on_delete=models.PROTECT,
        verbose_name="Member/Service Provider",
        help_text="Set this only if the member is different from the owner of the " +
        "parent Network Service (e.g. if this L3 connection is a peering connection).",
        null=True,
        blank=True,
    )

    member_site = models.ForeignKey(
        'dcim.Site',
        verbose_name='Member/Service Provider Site',
        on_delete=models.PROTECT,
        help_text="Set this only if the member is different from the owner of the " +
        "parent Network Service (e.g. if this L3 connection is a peering connection).",
        null=True,
        blank=True,
    )

    logical_system = models.ForeignKey(
        to='sidekick.LogicalSystem',
        on_delete=models.PROTECT,
        related_name='network_service_l3',
        null=True,
        blank=True,
    )

    routing_type = models.ForeignKey(
        to='sidekick.RoutingType',
        on_delete=models.PROTECT,
        related_name='network_service_l3',
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

    ipv4_prefixes = models.TextField(
        verbose_name='IPv4 Prefixes',
        help_text='IPv4 Prefixes of the member',
        null=True,
        blank=True,
    )

    provider_router_address_ipv4 = models.CharField(
        max_length=255,
        verbose_name='Provider Router Address IPv4',
        help_text='The IPv4 Address of the NREN/Provider',
        blank=True,
        default='',
    )

    member_router_address_ipv4 = models.CharField(
        max_length=255,
        verbose_name='Member Router Address IPv4',
        help_text='The IPv4 Address of the Member',
        blank=True,
        default='',
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

    ipv6_prefixes = models.TextField(
        verbose_name='IPv6 Prefixes',
        help_text='IPv6 Prefixes of the member',
        null=True,
        blank=True,
    )

    provider_router_address_ipv6 = models.CharField(
        max_length=255,
        verbose_name='Provider Router Address IPv6',
        help_text='The IPv6 Address of the NREN/Provider',
        blank=True,
        default='',
    )

    member_router_address_ipv6 = models.CharField(
        max_length=255,
        verbose_name='Member Router Address IPv6',
        help_text='The IPv6 Address of the Member',
        blank=True,
        default='',
    )

    comments = models.TextField(
        verbose_name='Comments',
        help_text='Additional comments about the service',
        blank=True,
    )

    legacy_id = models.CharField(
        max_length=255,
        verbose_name='Old ID for migrations',
        help_text='The ID of the l3 service in an old system',
        blank=True,
        default='',
    )

    active = models.BooleanField(
        verbose_name='Active',
        help_text='The active/inactive status of the L3 service',
        default=True,
    )

    ip_prefixes = models.ManyToManyField(
        Prefix,
        verbose_name='IP Prefixes',
        blank=True,
    )

    class Meta:
        verbose_name = "Network Service L3"
        verbose_name_plural = "Network Services L3"

    def __str__(self):
        if self.member is not None:
            return f"{self.member} via {self.network_service_device.network_service.name}"
        return f"{self.network_service_device} L3 Service"

    def get_peeringconnection_url(self):
        return reverse('plugins:sidekick:peeringconnection_detail', args=[self.pk])

    def get_absolute_url(self):
        return reverse('plugins:sidekick:networkservicel3_detail', args=[self.pk])


# NetworkServiceGroup represents a grouping of network services
# that have a common theme. For example: K-12 Members
class NetworkServiceGroup(NetBoxModel):
    name = models.CharField(
        max_length=50,
        unique=True,
        verbose_name='Name',
        help_text='The name of the network service group',
    )

    slug = models.SlugField(
        unique=True,
    )

    description = models.CharField(
        max_length=255,
        verbose_name='Description',
        help_text='A description of the network service group',
        blank=True,
        default='',
    )

    network_services = models.ManyToManyField(NetworkService)

    class Meta:
        ordering = ['name']
        verbose_name = 'Network Service Group'
        verbose_name_plural = 'Network Service Groups'

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('plugins:sidekick:networkservicegroup_detail', args=[self.pk])
