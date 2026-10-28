"""Member entitlement: what an account may act for.

One place answers the question, so the portal, the MCP front door and any report get the
same answer. Everything here fails closed: an account with no rows, an address with no
account, and an unresolvable username all produce an empty set plus a reason, never a
default. A resolver that guesses grants one member's rows to another.

The address is the key. NetBox username and email both hold the person's address for
member accounts, but the username is what `RemoteUserBackend` matches, so that is what
this module reads. Comparison is case-insensitive because the address as entered may not
be lowercased, and a case-sensitive match would lock a real person out.
"""

import re

from sidekick.models import MemberTenant

# Refusal reasons. Each names the guard that fired so a caller can say why rather than
# reporting an empty list, which reads as "you have no members" even when the address was
# simply never registered.
REASON_OK = 'entitled'
REASON_NO_ACCOUNT = 'no account for this address'
REASON_INACTIVE = 'account is not active'
REASON_NO_ENTITLEMENT = 'account holds no member entitlement'


def resolve_entitlement(address):
    """The members an address may act for, and why that answer was given.

    Returns a dict with `tenants` (a list of Tenant objects), `roles` (tenant id to role),
    `reason` and, when it resolved, the `user` it resolved to.
    """
    from django.contrib.auth import get_user_model

    if not address or '@' not in address:
        return {'tenants': [], 'roles': {}, 'reason': REASON_NO_ACCOUNT, 'user': None}

    User = get_user_model()
    # Username first because that is what RemoteUserBackend matches; email is the
    # fallback for an account whose username is not the address.
    user = (
        User.objects.filter(username__iexact=address).first()
        or User.objects.filter(email__iexact=address).first()
    )
    if user is None:
        return {'tenants': [], 'roles': {}, 'reason': REASON_NO_ACCOUNT, 'user': None}
    if not user.is_active:
        return {'tenants': [], 'roles': {}, 'reason': REASON_INACTIVE, 'user': user}

    rows = list(
        MemberTenant.objects.filter(user=user)
        .select_related('tenant')
        .order_by('tenant__name')
    )
    if not rows:
        return {
            'tenants': [], 'roles': {}, 'reason': REASON_NO_ENTITLEMENT, 'user': user,
        }

    return {
        'tenants': [row.tenant for row in rows],
        'roles': {row.tenant_id: row.role for row in rows},
        'reason': REASON_OK,
        'user': user,
    }


def normalise_member_name(name):
    """A tenant name and a group name reduced to what should compare equal.

    The convention this replaces compared the two strings exactly, so a tenant
    renamed with a `- disabled` suffix stopped matching its group and access changed
    silently: 16 tenant/group pairs had drifted by 2026-10-28. This normaliser is used
    once, to seed entitlements from the groups that exist, and to report what did not
    resolve. Nothing at request time depends on names.
    """
    if not name:
        return ''
    name = re.sub(r'\s*[-\u2013]\s*disabled\s*$', '', name.strip(), flags=re.IGNORECASE)
    name = name.replace('&', 'and').replace("'", '').replace('\u2019', '')
    return re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-')


def entitled_tenant_ids(address):
    """Just the tenant ids, for a caller that has its own reason strings."""
    return [tenant.pk for tenant in resolve_entitlement(address)['tenants']]
