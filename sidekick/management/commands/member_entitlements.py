"""Seed member entitlements from the group convention, and report what does not fit.

Until now an account could act for a member because a Django auth group carried the
member's name. That convention has no changelog, breaks on a rename, and cannot say what
kind of grant it is. This command writes the rows that replace it, and nothing else: it
does not touch groups, so it can be run, reviewed and re-run while the old convention is
still in place.

Dry run by default. Every count is printed either way, so the report and the write come
from the same pass over the same data.

What it will not do is guess. A group whose name matches no member tenant is reported and
skipped, because inventing a tenant would grant access nobody asked for. Accounts that
resolve to no member are reported too: fail-closed resolution turns them into refused
requests, and the team should see the list before that happens.
"""

from collections import defaultdict

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction

from tenancy.models import Tenant
from users.models import Group

from sidekick.models import MemberTenant
from sidekick.utils.membership import normalise_member_name

# The rows this command writes leave no note. The provenance ("came from group X") is
# recorded in the run's output and, after 2026-10-28, in nothing else: the groups it refers
# to have been deleted, so a note naming one is stale, and 223 rows carried it into the
# member page where it read as a decision nobody made.
SEED_NOTE = ""


class Command(BaseCommand):
    help = 'Create member entitlement rows from existing group membership (dry run by default)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--apply', action='store_true',
            help='Write the rows. Without this the command only reports.',
        )
        parser.add_argument(
            '--recreate-groups', action='store_true',
            help='Rollback path: recreate the tenant-named groups from the rows.',
        )

    def handle(self, *args, **options):
        if options['recreate_groups']:
            return self.recreate_groups(apply=options['apply'])

        User = get_user_model()
        members = Tenant.objects.filter(group__name='Members')
        by_name = {}
        for tenant in members:
            by_name.setdefault(normalise_member_name(tenant.name), tenant)

        # group name -> tenant, for the report
        group_tenant = {}
        unresolved_groups = []
        for group in Group.objects.all():
            tenant = by_name.get(normalise_member_name(group.name))
            if tenant is None:
                unresolved_groups.append(group.name)
            else:
                group_tenant[group.name] = tenant

        plan = []            # (user, tenant, group name)
        unresolved_grants = []
        for user in User.objects.prefetch_related('groups'):
            for group in user.groups.all():
                tenant = group_tenant.get(group.name)
                if tenant is None:
                    unresolved_grants.append((user.username, group.name))
                else:
                    plan.append((user, tenant, group.name))

        existing = set(MemberTenant.objects.values_list('user_id', 'tenant_id'))
        to_create = [row for row in plan if (row[0].pk, row[1].pk) not in existing]

        ungrouped = [
            user.username for user in User.objects.filter(is_active=True).prefetch_related('groups')
            if '@' in user.username and not user.groups.exists() and
            not user.username.lower().endswith('cybera.ca')
        ]
        resolved_names = {normalise_member_name(name) for name in group_tenant}
        tenants_without_group = sorted(
            tenant.name for tenant in members
            if normalise_member_name(tenant.name) not in resolved_names
        )
        per_user = defaultdict(int)
        for user, _tenant, _group in plan:
            per_user[user.username] += 1

        self.stdout.write(f"Member tenants: {members.count()}")
        self.stdout.write(f"Groups: {Group.objects.count()} "
                          f"({len(group_tenant)} resolve to a member, "
                          f"{len(unresolved_groups)} do not)")
        self.stdout.write(f"Grants derived from group membership: {len(plan)}")
        self.stdout.write(f"  already present: {len(plan) - len(to_create)}")
        self.stdout.write(f"  to create: {len(to_create)}")
        self.stdout.write(f"Accounts holding more than one grant: "
                          f"{sum(1 for n in per_user.values() if n > 1)}")

        if unresolved_grants:
            self.stdout.write('\nGrants that resolve to no member (skipped, need a decision):')
            for username, group in unresolved_grants:
                self.stdout.write(f'  {username:45} group={group}')

        if tenants_without_group:
            self.stdout.write('\nMember tenants with no group of the same name:')
            for name in tenants_without_group:
                self.stdout.write(f'  {name}')

        if ungrouped:
            self.stdout.write('\nActive member accounts in no group (they will be entitled to nothing):')
            for username in ungrouped:
                self.stdout.write(f'  {username}')

        if not options['apply']:
            self.stdout.write('\nDry run. Nothing written. Re-run with --apply to create the rows.')
            return

        with transaction.atomic():
            created = 0
            for user, tenant, group in to_create:
                MemberTenant.objects.create(
                    user=user,
                    tenant=tenant,
                    note=SEED_NOTE,
                )
                created += 1
        self.stdout.write(f'\nCreated {created} entitlement rows.')

    def recreate_groups(self, apply=False):
        """Rebuild the tenant-named groups from the rows, for a rollback.

        Deliberately reports only unless --apply is given: this path exists so that
        deleting the groups can be undone, and it should never run by accident.
        """
        plan = []
        for row in MemberTenant.objects.select_related('user', 'tenant'):
            plan.append((row.tenant.name, row.user.username))

        names = sorted({name for name, _username in plan})
        self.stdout.write(f'Groups to recreate: {len(names)}')
        for name in names:
            self.stdout.write(f'  {name}')

        if not apply:
            self.stdout.write('\nDry run. Nothing written. Re-run with --apply to recreate the groups.')
            return

        created = 0
        with transaction.atomic():
            for name in names:
                group, was_created = Group.objects.get_or_create(name=name)
                if was_created:
                    created += 1
                usernames = [u for n, u in plan if n == name]
                # NetBox replaces Django's auth models, so the group's members are
                # reachable as `user_set` only on a stock Django Group. Assign the
                # reverse side of the M2M instead, which both models have.
                for user in get_user_model().objects.filter(username__in=usernames):
                    user.groups.add(group)
        self.stdout.write(f'\nRecreated {created} groups.')
