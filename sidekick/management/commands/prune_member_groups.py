"""Delete the tenant-named auth groups that used to carry member access.

The groups exist only because access used to be a group whose name equalled a tenant
name. Access is now a `MemberTenant` row, so the groups decide nothing: the portal, the
Member Contacts view and the MCP servers all read the rows. This command is the last
step of that migration and the only irreversible one, so it reports before it deletes,
writes a snapshot of what it is about to remove, and refuses to proceed while a group
still holds a user who has no row for that member.

Dry run by default. `--apply` deletes; `--force` overrides the safety refusal, and the
refusal exists so that nobody drops a user's last recorded access without reading the
list first.

The deletion is stored in no changelog, because `users.Group` is not a NetBox model.
That is why `--snapshot` writes the mapping to a file: rollback is
`member_entitlements --recreate-groups --apply`, and the snapshot is the evidence of
what the groups held at the moment they went.
"""

import json

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction

from tenancy.models import Tenant
from users.models import Group

from sidekick.models import MemberTenant
from sidekick.utils.membership import normalise_member_name

# Groups that carry permission meaning rather than a member name. `read-only` holds the
# object permissions that let member accounts read their own data; deleting it would
# remove real access.
KEEP_GROUPS = {'read-only'}


class Command(BaseCommand):
    help = 'Delete tenant-named auth groups now that entitlement is a row (dry run by default)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--apply', action='store_true',
            help='Delete the groups. Without this the command only reports.',
        )
        parser.add_argument(
            '--force', action='store_true',
            help='Delete even though a group holds a user with no entitlement row.',
        )
        parser.add_argument(
            '--snapshot', default='',
            help='Write the groups, their member and their members to this JSON file before deleting.',
        )

    def handle(self, *args, **options):
        User = get_user_model()

        by_name = {}
        for tenant in Tenant.objects.filter(group__name='Members'):
            by_name.setdefault(normalise_member_name(tenant.name), tenant)

        groups = list(Group.objects.all().order_by('name'))
        doomed = []        # (group, tenant)
        kept = []          # (group, reason)
        for group in groups:
            if group.name in KEEP_GROUPS:
                kept.append((group, 'carries permissions'))
                continue
            tenant = by_name.get(normalise_member_name(group.name))
            if tenant is None:
                kept.append((group, 'matches no member tenant'))
                continue
            doomed.append((group, tenant))

        granted = set(MemberTenant.objects.values_list('user_id', 'tenant_id'))
        snapshot = []
        blockers = []      # (username, group, tenant)
        empty = 0
        for group, tenant in doomed:
            # Filter from the user side: NetBox replaces the auth models, so the reverse
            # accessor on Group is not guaranteed to exist.
            members = list(User.objects.filter(groups=group).order_by('username'))
            if not members:
                empty += 1
            for user in members:
                if (user.pk, tenant.pk) not in granted:
                    blockers.append((user.username, group.name, tenant.name))
            snapshot.append({
                'group': group.name,
                'tenant_id': tenant.pk,
                'tenant': tenant.name,
                'users': [user.username for user in members],
            })

        self.stdout.write(f'Groups: {len(groups)}')
        self.stdout.write(f'  to delete: {len(doomed)} ({empty} of them empty)')
        self.stdout.write(f'  to keep: {len(kept)}')
        for group, reason in kept:
            self.stdout.write(f'    {group.name:45} {reason}')

        users_in_doomed = sum(len(row['users']) for row in snapshot)
        self.stdout.write(f'Group memberships under the groups to delete: {users_in_doomed}')
        self.stdout.write(f'Member entitlement rows: {MemberTenant.objects.count()}')

        if blockers:
            self.stdout.write('\nGroup members with no entitlement row for that member:')
            for username, group_name, tenant_name in blockers:
                self.stdout.write(f'  {username:45} group={group_name} -> {tenant_name}')
            self.stdout.write(
                '\nThese accounts are in a tenant-named group but hold no row for that member, so the\n'
                'group is the only trace of the access they used to have. Nothing reads it, so\n'
                'deleting the group changes nothing that runs -- but if that access should still\n'
                'exist, create the row first. Re-run with --force to delete anyway.'
            )

        if options['snapshot']:
            with open(options['snapshot'], 'w') as handle:
                json.dump({'groups': snapshot, 'kept': [g.name for g, _r in kept]},
                          handle, indent=2, sort_keys=True)
            self.stdout.write(f'\nSnapshot written to {options["snapshot"]}')

        if not options['apply']:
            self.stdout.write('\nDry run. Nothing deleted. Re-run with --apply to delete the groups.')
            return

        if blockers and not options['force']:
            self.stdout.write('\nRefusing to delete while the list above is not empty. Nothing deleted.')
            return

        with transaction.atomic():
            for group, _tenant in doomed:
                group.delete()

        self.stdout.write(f'\nDeleted {len(doomed)} groups. '
                          f'{Group.objects.count()} groups remain.')
        self.stdout.write('Rollback: member_entitlements --recreate-groups --apply')
