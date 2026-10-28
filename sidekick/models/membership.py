from django.db import models
from django.urls import reverse

from netbox.models import NetBoxModel


class MemberTenant(NetBoxModel):
    """One account's entitlement to one member.

    This replaces the convention that a member's staff reach member data through a
    Django auth group whose name equals the tenant name. That convention is invisible
    to NetBox's changelog (`users.User`, `users.Group` and `users.ObjectPermission` have
    no changelog entries at all), so no grant or revocation was ever recorded, and a
    tenant rename silently changed who could see what. See ADR-100.

    The Django user stays the authentication anchor because the portal authenticates
    with `RemoteUserBackend`, matching `REMOTE_USER` against an existing user. This row
    is the authorisation record: who may act for which member, and in what role.

    A user may hold several rows. That is the case the group convention could not
    express for member accounts: one network administrator responsible for more than
    one member.
    """

    ROLE_VIEWER = 'viewer'
    ROLE_OPERATOR = 'operator'
    ROLE_ADMIN = 'admin'
    ROLE_CHOICES = (
        (ROLE_VIEWER, 'Viewer'),
        (ROLE_OPERATOR, 'Operator'),
        (ROLE_ADMIN, 'Administrator'),
    )

    user = models.ForeignKey(
        to='users.User',
        verbose_name='Account',
        # PROTECT: deleting an account must not quietly delete the record of what it
        # was entitled to. Remove the entitlement first, deliberately.
        on_delete=models.PROTECT,
        related_name='member_tenants',
        help_text='The account, whose username is the address it signs in with',
    )

    tenant = models.ForeignKey(
        to='tenancy.Tenant',
        verbose_name='Member',
        # PROTECT, like AccountingProfile.member and TransitRate.tenant: a tenant
        # delete must not take the access record with it.
        on_delete=models.PROTECT,
        related_name='member_tenants',
    )

    role = models.CharField(
        verbose_name='Role',
        max_length=16,
        choices=ROLE_CHOICES,
        default=ROLE_VIEWER,
        help_text='What this account may do, once there is anything to do beyond reading',
    )

    note = models.TextField(
        verbose_name='Note',
        blank=True,
        help_text='The ticket, the request, or why this account may act for this member',
    )

    class Meta:
        # NetBox 4.x paginates only ordered querysets; an unordered one raises
        # QuerySetNotOrdered and returns HTTP 500.
        ordering = ['tenant', 'user']
        verbose_name = 'Member Entitlement'
        verbose_name_plural = 'Member Entitlements'
        constraints = (
            models.UniqueConstraint(
                fields=('user', 'tenant'),
                name='sidekick_membertenant_unique_user_tenant',
            ),
        )

    def __str__(self):
        return f"{self.user} → {self.tenant}"

    def get_absolute_url(self):
        return reverse('plugins:sidekick:membertenant', args=[self.pk])

    def get_role_color(self):
        return {
            self.ROLE_VIEWER: 'gray',
            self.ROLE_OPERATOR: 'blue',
            self.ROLE_ADMIN: 'red',
        }.get(self.role, 'gray')
