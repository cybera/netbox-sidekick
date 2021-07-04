from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify

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
        return reverse('plugins:sidekick:accountingclass_detail', args=[self.pk])

    def graphite_name(self):
        return slugify(self.name)

    def graphite_destination_name(self):
        return slugify(self.destination)


# AccountingClassCounter represents counters for an AccountingClass from a device.
class AccountingClassCounter(ChangeLoggedModel):
    accounting_class = models.ForeignKey(
        'sidekick.AccountingClass',
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
        verbose_name = 'Accounting Class Counter'
        verbose_name_plural = 'Accounting Class Counters'

    def __str__(self):
        return f"{self.accounting_class}: {self.scu}/{self.dcu}"

    def get_absolute_url(self):
        return reverse('plugins:sidekick:accountingclasscounter_detail', args=[self.pk])

    # If there are more than 5 entries for an AccountingClassCounter,
    # delete older ones.
    def save(self, *args, **kwargs):
        previous_entries = AccountingClassCounter.objects.filter(
            accounting_class_id=self.accounting_class_id).order_by('-last_updated')
        for entry in previous_entries[4:]:
            entry.delete()

        super().save(*args, **kwargs)


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
        return reverse('plugins:sidekick:accountingprofile_detail', args=[self.pk])

    def get_current_bandwidth_profile(self):
        return self.bandwidthprofile_set.filter(
            effective_date__lte=timezone.now()).order_by('-effective_date').first()


# BandwidthProfile represents a bandwidth setting for a member.
class BandwidthProfile(ChangeLoggedModel):
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

    class Meta:
        ordering = ['accounting_profile']
        verbose_name = 'Bandwidth Profile'
        verbose_name_plural = 'Bandwidth Profiles'

    def __str__(self):
        return f"{self.accounting_profile}: {self.traffic_cap}"

    def get_absolute_url(self):
        return reverse('plugins:sidekick:bandwidthprofile_detail', args=[self.pk])
