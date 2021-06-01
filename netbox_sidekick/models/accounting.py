from django.db import models
from django.urls import reverse
from django.utils import timezone

from extras.models import ChangeLoggedModel


# AccountingClass represents an SCU/DCU class from a device.
class AccountingClass(ChangeLoggedModel):
    device = models.ForeignKey(
        'dcim.Device',
        verbose_name='Device',
        on_delete=models.PROTECT,
    )

    name = models.CharField(
        max_length=255,
        verbose_name='Name',
        help_text='The name of the SCU/DCU profile',
    )

    destination = models.CharField(
        max_length=255,
        verbose_name='Name',
        help_text='The name of the destination profile',
    )

    class Meta:
        ordering = ['device', 'name', 'destination']
        verbose_name = 'Accounting Class'
        verbose_name_plural = 'Accounting Classes'

    def __str__(self):
        return f"{self.device.name}: {self.name} -- {self.destination}"

    def get_absolute_url(self):
        return reverse('plugins:netbox_sidekick:accountingclass_detail', args=[self.pk])


# AccountingProfile represents a Member with tracked bandwidth
class AccountingProfile(ChangeLoggedModel):
    member = models.ForeignKey(
        'tenancy.Tenant',
        on_delete=models.PROTECT,
    )

    accounting_classes = models.ManyToManyField(AccountingClass)

    name = models.CharField(
        max_length=255,
        verbose_name='Profile Name',
        help_text='An optional name for the profile',
        blank=True,
        null=True,
    )

    enabled = models.BooleanField(
        verbose_name='Enabled',
        help_text='If the profile is enabled or disabled',
        default=True,
    )

    comments = models.TextField(
        verbose_name='Comments',
        help_text='Comments about the profile',
        blank=True,
        null=True,
    )

    class Meta:
        ordering = ['member', 'name']
        verbose_name = 'Accounting Profile'
        verbose_name_plural = 'Accounting Profiles'

    def __str__(self):
        if self.name is not None and self.name != "":
            return f"{self.member.name}: {self.name}"
        else:
            return f"{self.member.name}"

    def get_absolute_url(self):
        return reverse('plugins:netbox_sidekick:accountingprofile_detail', args=[self.pk])

    def get_current_bandwidth_profile(self):
        return self.bandwidthprofile_set.latest('effective_date')


# BandwidthProfile represents a bandwidth setting for a member.
class BandwidthProfile(ChangeLoggedModel):
    accounting_profile = models.ForeignKey(
        'netbox_sidekick.AccountingProfile',
        on_delete=models.PROTECT,
    )

    effective_date = models.DateField(
        verbose_name='Effective Date',
        help_text='The date when the profile goes into effect',
        blank=True,
        null=True,
        default=timezone.now,
    )

    comments = models.TextField(
        verbose_name='Comments',
        help_text='Comments about the profile',
        blank=True,
        null=True,
    )

    traffic_cap = models.BigIntegerField(
        verbose_name='Traffic Cap',
        help_text='The traffic cap of the profile in megabits',
        blank=True,
        null=True,
    )

    burst_limit = models.BigIntegerField(
        verbose_name='Burst Limit',
        help_text='The burst limit of the profile in megabits',
        blank=True,
        null=True,
    )

    class Meta:
        ordering = ['accounting_profile']
        verbose_name = 'Bandwidth Profile'
        verbose_name_plural = 'Bandwidth Profiles'

    def __str__(self):
        return f"{self.accounting_profile}: {self.traffic_cap}"

    def get_absolute_url(self):
        return reverse('plugins:netbox_sidekick:bandwidthprofile_detail', args=[self.pk])
