"""Stored addresses are lowercase.

An account's username is the address the person signs in with, and the portal's
`RemoteUserBackend` matches `REMOTE_USER` against it. A user row saved with an uppercase
character therefore works only until the identity provider releases the address in
another case, at which point a real person cannot log in. Measured on 2026-10-28: one row
in 328 was not lowercase, and it was a duplicate of an existing account.

This is enforcement on write. The resolver also compares case-insensitively, so a row
that predates this hook still resolves; the two are deliberate belt and braces.
"""

from django.contrib.auth import get_user_model
from django.db.models.signals import pre_save
from django.dispatch import receiver


@receiver(pre_save, sender='users.User')
def lowercase_account_addresses(sender, instance, **kwargs):
    for field in ('username', 'email'):
        value = getattr(instance, field, None)
        if not value:
            continue
        lowered = value.lower()
        if lowered != value:
            setattr(instance, field, lowered)
