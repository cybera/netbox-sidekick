"""Member transit billing: cap times rate.

The two inputs live in different places by design.

The cap is measured and historical: `BandwidthProfile.traffic_cap` on the member's
AccountingProfile, effective-dated, with a `billable` flag. The rate is a commercial
term: a global default in `TransitRate` with optional per-member overrides, also
effective-dated. Nothing here reads flow data; 95th percentile is a capacity measure,
not a billing figure.

`FALLBACK_RATE_PER_MBIT` exists only so an unconfigured database still returns an
answer instead of zero. Its use is reported as `rate_source == 'fallback'` so a caller
can tell a configured rate from an unconfigured one.
"""

from decimal import Decimal

from django.utils import timezone

from sidekick.models import TransitRate

FALLBACK_RATE_PER_MBIT = Decimal('1.20')


def resolve_transit_rate(tenant, as_of=None):
    """The rate in force for `tenant` on `as_of`, and where it came from.

    An override wins over the global default. Among rows of the same kind the most
    recent effective date wins. Returns a dict rather than a bare number so the
    caller can say which rate was used, which is the difference between "AHS pays
    $0.65" and "AHS is being priced at the default".
    """
    as_of = as_of or timezone.localdate()
    effective = TransitRate.objects.filter(effective_date__lte=as_of)

    if tenant is not None:
        override = effective.filter(tenant=tenant).order_by('-effective_date', '-pk').first()
        if override is not None:
            return {
                'rate_per_mbit': override.rate_per_mbit,
                'rate_source': 'member override',
                'effective_date': override.effective_date,
                'rate_id': override.pk,
            }

    default = effective.filter(tenant__isnull=True).order_by('-effective_date', '-pk').first()
    if default is not None:
        return {
            'rate_per_mbit': default.rate_per_mbit,
            'rate_source': 'global default',
            'effective_date': default.effective_date,
            'rate_id': default.pk,
        }

    return {
        'rate_per_mbit': FALLBACK_RATE_PER_MBIT,
        'rate_source': 'fallback',
        'effective_date': None,
        'rate_id': None,
    }


def billable_caps(tenant, as_of=None):
    """Current billable traffic cap per accounting profile, in megabits.

    A member may have several accounting profiles, each with its own cap, so the
    billable quantity is their sum. Only rows that are billable, carry a cap, and are
    in force on `as_of` count; the most recent such row per profile wins.
    """
    as_of = as_of or timezone.localdate()
    out = []
    for profile in tenant.accountingprofile_set.all():
        row = (
            profile.bandwidthprofile_set
            .filter(billable=True, traffic_cap__isnull=False, effective_date__lte=as_of)
            .order_by('-effective_date', '-pk')
            .first()
        )
        if row is None:
            continue
        out.append(
            {
                'accounting_profile_id': profile.pk,
                'accounting_profile': str(profile),
                'bandwidth_profile_id': row.pk,
                'traffic_cap_mbit': row.traffic_cap,
                'burst_limit_mbit': row.burst_limit,
                'effective_date': row.effective_date,
            }
        )
    return out


def member_billing(tenant, as_of=None):
    """What this member's transit costs at their purchased cap, and why."""
    as_of = as_of or timezone.localdate()
    caps = billable_caps(tenant, as_of)
    rate = resolve_transit_rate(tenant, as_of)
    total_cap = sum(cap['traffic_cap_mbit'] for cap in caps)
    return {
        'member': tenant.name,
        'member_id': tenant.pk,
        'as_of': as_of,
        'cap_mbit': total_cap,
        'rate_per_mbit': rate['rate_per_mbit'],
        'rate_source': rate['rate_source'],
        'rate_effective_date': rate['effective_date'],
        'rate_id': rate['rate_id'],
        'monthly_cost': (Decimal(total_cap) * rate['rate_per_mbit']) if total_cap else Decimal('0'),
        'caps': caps,
    }
