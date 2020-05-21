from django.contrib.auth.models import Group
from django.db import models
from django.urls import reverse
from django.utils import timezone

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


# MemberType represents different types of a Member.
# For example: Internet Exchange, K-12, Post-Secondary.
class MemberType(ChangeLoggedModel):
    name = models.CharField(
        max_length=255,
        unique=True,
        verbose_name='Type',
        help_text='A type to represent a group of members',
    )

    slug = models.SlugField(
        unique=True,
    )

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('plugins:netbox_sidekick:membertype_detail', args=[self.slug])


# Member represents a member of the organization.
#
# This model acts as an extension to a NetBox Tenant.
# Technically, this model could be implemented with Custom Fields, but having
# it as a model creates a standardization.
#
# In addition, it links to an authenticated user, allowing us to bridge
# members with login accounts to NetBox.
class Member(ChangeLoggedModel):
    tenant = models.OneToOneField(
        'tenancy.Tenant',
        on_delete=models.PROTECT,
    )

    auth_group = models.ForeignKey(
        Group,
        blank=True,
        null=True,
        on_delete=models.PROTECT,
    )

    member_type = models.ForeignKey(
        to='netbox_sidekick.MemberType',
        on_delete=models.PROTECT,
        verbose_name='Member Type',
    )

    active = models.BooleanField(
        verbose_name='Active',
        help_text='The status of the member',
        default=True,
    )

    billing_exempt = models.BooleanField(
        verbose_name='Exempt from Billing',
        help_text='This member does not get billed',
        default=False,
    )

    start_date = models.DateField(
        verbose_name='Start Date',
        help_text='The date the member joined',
        blank=True,
        default=timezone.now,
    )

    invoice_period_start = models.CharField(
        max_length=255,
        verbose_name='Invoice Period Start',
        help_text='The month of the start of the invoice cycle',
        blank=True,
        default='',
    )

    number_of_users = models.IntegerField(
        verbose_name='Number of Users',
        help_text='The number of users (FTE/FLE)',
        blank=True,
        default=0,
    )

    billing_contact_first_name = models.CharField(
        max_length=255,
        verbose_name='Billing Contact First Name',
        help_text='The first name of the billing contact',
        blank=True,
        default='',
    )

    billing_contact_last_name = models.CharField(
        max_length=255,
        verbose_name='Billing Contact Last Name',
        help_text='The last name of the billing contact',
        blank=True,
        default='',
    )

    billing_contact_title = models.CharField(
        max_length=255,
        verbose_name='Billing Contact Title',
        help_text='The title of the billing contact',
        blank=True,
        default='',
    )

    billing_contact_phone_number = models.CharField(
        max_length=255,
        verbose_name='Billing Contact Phone Number',
        help_text='The phone number of the billing contact',
        blank=True,
        default='',
    )

    billing_contact_email_address = models.EmailField(
        verbose_name='Billing Contact Email Address',
        help_text='The email address of the billing contact',
        blank=True,
        default='',
    )

    billing_address_1 = models.CharField(
        max_length=255,
        verbose_name='Billing Address 1',
        help_text='Billing Address 1',
        blank=True,
        default='',
    )

    billing_address_2 = models.CharField(
        max_length=255,
        verbose_name='Billing Address 2',
        help_text='Billing Address 2',
        blank=True,
        default='',
    )

    billing_city = models.CharField(
        max_length=255,
        verbose_name='Billing City',
        help_text='Billing City',
        blank=True,
        default='',
    )

    billing_postal_code = models.CharField(
        max_length=255,
        verbose_name='Billing Postal Code',
        help_text='Billing Postal Code',
        blank=True,
        default='',
    )

    billing_province = models.CharField(
        max_length=255,
        verbose_name='Billing Province',
        help_text='Billing Province',
        blank=True,
        default='',
    )

    billing_country = models.CharField(
        max_length=255,
        verbose_name='Billing Country',
        help_text='Billing Country',
        blank=True,
        default='',
    )

    technical_contact_first_name = models.CharField(
        max_length=255,
        verbose_name='Technical Contact First Name',
        help_text='The first name of the technical contact',
        blank=True,
        default='',
    )

    technical_contact_last_name = models.CharField(
        max_length=255,
        verbose_name='Technical Contact Last Name',
        help_text='The last name of the technical contact',
        blank=True,
        default='',
    )

    technical_contact_title = models.CharField(
        max_length=255,
        verbose_name='Technical Contact Title',
        help_text='The title of the technical contact',
        blank=True,
        default='',
    )

    technical_contact_phone_number = models.CharField(
        max_length=255,
        verbose_name='Technical Contact Phone Number',
        help_text='The phone number of the technical contact',
        blank=True,
        default='',
    )

    technical_contact_email_address = models.EmailField(
        verbose_name='Technical Contact Email Address',
        help_text='The email address of the technical contact',
        blank=True,
        default='',
    )

    url = models.URLField(
        blank=True,
        default=''
    )

    supernet = models.BooleanField(
        verbose_name='Connected via Supernet?',
        help_text='Is the member connected via supernet?',
        blank=True,
        default=True,
    )

    latitude = models.FloatField(
        verbose_name='Latitude',
        help_text="Latitude of the member's location",
        blank=True,
        default=0,
    )

    longitude = models.FloatField(
        verbose_name='Longitude',
        help_text="Longitude of the member's location",
        blank=True,
        default=0,
    )

    comments = models.TextField(
        verbose_name='Comments',
        help_text='Additional comments about the member',
        blank=True,
        default='',
    )

    class Meta:
        ordering = ['member_type', 'tenant']

    def __str__(self):
        return self.tenant.description

    def get_absolute_url(self):
        return reverse('plugins:netbox_sidekick:member_detail', args=[self.pk])


# MemberNodeType represents a type of member node.
class MemberNodeType(ChangeLoggedModel):
    name = models.CharField(
        max_length=255,
        unique=True,
        verbose_name='Type',
        help_text='A type to represent a group of member nodes',
    )

    slug = models.SlugField(
        unique=True,
    )

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('plugins:netbox_sidekick:membernodetype_detail', args=[self.slug])


# MemberNode represents a POP/Node of a Tenant.
# We use "tenant" for ownership instead of Member
# because some nodes are owned by non-members but
# then connect members.
class MemberNode(ChangeLoggedModel):
    owner = models.ForeignKey(
        'tenancy.Tenant',
        on_delete=models.PROTECT,
    )

    name = models.CharField(
        max_length=255,
        verbose_name='Name',
        help_text='The name of the node',
        blank=True,
        default='',
    )

    label = models.CharField(
        max_length=255,
        verbose_name='Label',
        help_text='A short name for the node',
        blank=True,
        default='',
    )

    internal_id = models.CharField(
        max_length=255,
        verbose_name='Internal ID',
        help_text='An internal ID for the node',
        blank=True,
        default='',
    )

    latitude = models.FloatField(
        verbose_name='Latitude',
        help_text="Latitude of the node's location",
        blank=True,
        default=0,
    )

    longitude = models.FloatField(
        verbose_name='Longitude',
        help_text="Longitude of the node's location",
        blank=True,
        default=0,
    )

    altitude = models.FloatField(
        verbose_name='Altitude',
        help_text="Altitude of the node's location",
        blank=True,
        default=0,
    )

    address = models.CharField(
        max_length=255,
        verbose_name='Address',
        help_text='A short address of the node',
        blank=True,
        default='',
    )

    node_type = models.ForeignKey(
        to='netbox_sidekick.MemberNodeType',
        on_delete=models.PROTECT,
        verbose_name='Node Type',
    )

    class Meta:
        ordering = ['owner', 'name']

    def __str__(self):
        if self.name != '':
            return f"{self.owner.description}: {self.name}"
        else:
            return self.owner.description

    def get_absolute_url(self):
        return reverse('plugins:netbox_sidekick:membernode_detail', args=[self.pk])


# MemberNodeLinkType represents a type of member node link.
class MemberNodeLinkType(ChangeLoggedModel):
    name = models.CharField(
        max_length=255,
        unique=True,
        verbose_name='Type',
        help_text='A type to represent a group of members node links',
    )

    slug = models.SlugField(
        unique=True,
    )

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('plugins:netbox_sidekick:membernodelinktype_detail', args=[self.slug])


# MemberNodeLink represents a link between two member nodes.
# We use "tenant" for ownership instead of Member
# because some nodes are owned by non-members but
# then connect members.
class MemberNodeLink(ChangeLoggedModel):
    owner = models.ForeignKey(
        'tenancy.Tenant',
        on_delete=models.PROTECT,
    )

    name = models.CharField(
        max_length=255,
        verbose_name='Name',
        help_text='The name of the node link',
        blank=True,
        default='',
    )

    label = models.CharField(
        max_length=255,
        verbose_name='Label',
        help_text='A short name for the node link',
        blank=True,
        default='',
    )

    internal_id = models.CharField(
        max_length=255,
        verbose_name='Internal ID',
        help_text='An internal ID for the node',
        blank=True,
        default='',
    )

    link_type = models.ForeignKey(
        'netbox_sidekick.MemberNodeLinkType',
        on_delete=models.PROTECT,
    )

    a_endpoint = models.ForeignKey(
        'netbox_sidekick.MemberNode',
        verbose_name='A Endpoint',
        related_name='a_endpoint',
        on_delete=models.PROTECT,
    )

    z_endpoint = models.ForeignKey(
        'netbox_sidekick.MemberNode',
        verbose_name='Z Endpoint',
        related_name='z_endpoint',
        on_delete=models.PROTECT,
    )

    throughput = models.FloatField(
        verbose_name='Throughput',
        help_text="Gigabits per second",
        blank=True,
        default=0,
    )

    class Meta:
        ordering = ['name']

    def __str__(self):
        if self.name != '':
            return f"{self.owner.description}: {self.name}"
        else:
            return self.owner.description

    def get_absolute_url(self):
        return reverse('plugins:netbox_sidekick:membernodelink_detail', args=[self.pk])
