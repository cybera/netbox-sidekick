from decimal import Decimal

from django.db import models
from django.urls import reverse
from django.utils import timezone

from netbox.models import NetBoxModel


class TransitRate(NetBoxModel):
    """A dollars-per-megabit rate for member transit.

    A row with no tenant is the global default rate. A row with a tenant is that
    member's override. Rows carry an effective date, like BandwidthProfile,
    because a rate is agreed for a contract term and a past bill must stay
    reproducible after the rate changes.

    The rate in force for a member on a given date is the most recent effective
    override, falling back to the most recent effective global default. That
    resolution lives in `sidekick.utils.billing.resolve_transit_rate` so the API,
    the UI and any report share one answer.
    """

    tenant = models.ForeignKey(
        'tenancy.Tenant',
        verbose_name='Member',
        # PROTECT, like AccountingProfile.member: a tenant delete must not silently
        # remove the record of what that member was billed.
        on_delete=models.PROTECT,
        related_name='transit_rates',
        blank=True,
        null=True,
        help_text='Leave blank to set the global default rate',
    )

    rate_per_mbit = models.DecimalField(
        verbose_name='Rate per Mbit',
        max_digits=8,
        decimal_places=4,
        help_text='Dollars per megabit, applied to the member traffic cap',
    )

    effective_date = models.DateField(
        verbose_name='Effective Date',
        default=timezone.localdate,
        help_text='The date from which this rate applies',
    )

    comments = models.TextField(
        verbose_name='Comments',
        blank=True,
        null=True,
    )

    class Meta:
        ordering = ['-effective_date', 'tenant', '-pk']
        verbose_name = 'Transit Rate'
        verbose_name_plural = 'Transit Rates'

    def __str__(self):
        who = self.tenant.name if self.tenant_id else 'Global default'
        return f"{who}: ${self.rate_per_mbit}/Mbit from {self.effective_date}"

    def get_absolute_url(self):
        return reverse('plugins:sidekick:transitrate', args=[self.pk])

    @property
    def is_global(self):
        return self.tenant_id is None

    def clean(self):
        super().clean()
        if self.rate_per_mbit is not None and self.rate_per_mbit < Decimal('0'):
            from django.core.exceptions import ValidationError
            raise ValidationError({'rate_per_mbit': 'A rate cannot be negative.'})
