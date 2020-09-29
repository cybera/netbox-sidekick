from django.contrib.auth.models import Group
from django.db import models
from django.urls import reverse
from django.utils import timezone

from extras.models import ChangeLoggedModel


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

    @property
    def member_count(self):
        return self.member_set.count()


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


class MemberContact(ChangeLoggedModel):
    member = models.ForeignKey(
        'netbox_sidekick.Member',
        on_delete=models.PROTECT,
    )

    contact = models.ForeignKey(
        'netbox_sidekick.Contact',
        on_delete=models.PROTECT,
    )

    type = models.ForeignKey(
        'netbox_sidekick.ContactType',
        on_delete=models.PROTECT,
    )

    class Meta:
        ordering = ['member', 'contact', 'type']

    def __str__(self):
        return f"{self.member} {self.type}: {self.contact}"

    def get_absolute_url(self):
        return reverse('plugins:netbox_sidekick:membercontact_detail', args=[self.pk])
