from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify

from netbox.models import NetBoxModel


# AccountingSource represents an SCU/DCU source from a device.
class AccountingSource(NetBoxModel):
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
        verbose_name = 'Accounting Source'
        verbose_name_plural = 'Accounting Sources'

    def __str__(self):
        return f"{self.device.name}: {self.name} -- {self.destination}"

    def get_absolute_url(self):
        return reverse('plugins:sidekick:accountingsource_detail', args=[self.pk])

    def graphite_name(self):
        return slugify(self.name)

    def graphite_path_name(self):
        return f"accounting.{slugify(self.name)}"

    def graphite_full_path_name(self):
        return f"{self.graphite_path_name()}.{slugify(self.destination)}"

    def graphite_destination_name(self):
        return slugify(self.destination)

    def get_current_rate(self):
        results = {
            'scu': 0,
            'dcu': 0,
        }

        entries = self.accountingsourcecounter_set.order_by('-last_updated')
        if len(entries) < 2:
            return results

        e1 = entries[0]
        e2 = entries[1]
        total_seconds = (e1.last_updated - e2.last_updated).total_seconds()

        for cat in ['scu', 'dcu']:
            m1 = getattr(e1, cat, None)
            m2 = getattr(e2, cat, None)
            if m1 is not None and m2 is not None:
                diff = (m1 - m2)
                if diff != 0:
                    diff = diff / total_seconds
                    results[cat] = diff

        return results


# AccountingSourceCounter represents counters for an AccountingSource from a device.
class AccountingSourceCounter(NetBoxModel):
    accounting_source = models.ForeignKey(
        'sidekick.AccountingSource',
        on_delete=models.PROTECT,
    )

    scu = models.BigIntegerField(
        verbose_name="SCU",
        help_text="SCU Bytes",
        default=0,
    )

    dcu = models.BigIntegerField(
        verbose_name="DCU",
        help_text="DCU Bytes",
        default=0,
    )

    class Meta:
        verbose_name = 'Accounting Source Counter'
        verbose_name_plural = 'Accounting Source Counters'

    def __str__(self):
        return f"{self.accounting_source}: {self.scu}/{self.dcu}"

    def get_absolute_url(self):
        return reverse('plugins:sidekick:accountingsourcecounter_detail', args=[self.pk])

    # If there are more than 5 entries for an AccountingSourceCounter,
    # delete older ones.
    def save(self, *args, **kwargs):
        previous_entries = AccountingSourceCounter.objects.filter(
            accounting_source_id=self.accounting_source_id).order_by('-last_updated')
        for entry in previous_entries[4:]:
            entry.delete()

        super().save(*args, **kwargs)


# AccountingProfile represents a Member with tracked bandwidth
class AccountingProfile(NetBoxModel):
    member = models.ForeignKey(
        'tenancy.Tenant',
        on_delete=models.PROTECT,
    )

    accounting_sources = models.ManyToManyField(AccountingSource, blank=True)

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
        return reverse('plugins:sidekick:accountingprofile_detail', args=[self.pk])

    def get_current_bandwidth_profile(self):
        return self.bandwidthprofile_set.filter(
            effective_date__lte=timezone.now()).order_by('-effective_date').first()

    def get_bandwidth_history(self):
        return self.bandwidthprofile_set.filter(
            effective_date__lte=timezone.now()).order_by('-effective_date')[1:]


# BandwidthProfile represents a bandwidth setting for a member.
class BandwidthProfile(NetBoxModel):
    accounting_profile = models.ForeignKey(
        'sidekick.AccountingProfile',
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

    billable = models.BooleanField(
        verbose_name='Billable',
        help_text='If this profile should be billed',
        default=True,
    )

    class Meta:
        ordering = ['accounting_profile']
        verbose_name = 'Bandwidth Profile'
        verbose_name_plural = 'Bandwidth Profiles'

    def __str__(self):
        return f"{self.accounting_profile}: {self.traffic_cap}"

    def get_absolute_url(self):
        return reverse('plugins:sidekick:bandwidthprofile_detail', args=[self.pk])
