"""Report, and optionally repair, account addresses that are not lowercase.

The signal in `sidekick/signals.py` lowercases on write, so this exists for the rows that
predate it and as a check a deploy can run. It reports by default and repairs only with
--apply, because changing a username changes how a person signs in: the portal matches
`REMOTE_USER` against it exactly.

A row whose lowercase form is already taken by another account is reported and left alone.
Merging two accounts is a decision for a person, not something this command should do.
"""

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction


class Command(BaseCommand):
    help = 'Report account addresses that are not lowercase (dry run by default)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--apply', action='store_true',
            help='Lowercase the addresses. Without this the command only reports.',
        )

    def handle(self, *args, **options):
        User = get_user_model()
        offenders = [
            user for user in User.objects.all()
            if (user.username or '') != (user.username or '').lower()
            or (user.email or '') != (user.email or '').lower()
        ]

        if not offenders:
            self.stdout.write('Every account address is lowercase.')
            return

        collisions = []
        fixable = []
        for user in offenders:
            lowered = user.username.lower()
            taken = User.objects.filter(username__iexact=lowered).exclude(pk=user.pk).exists()
            (collisions if taken else fixable).append(user)

        self.stdout.write(f'Accounts whose address is not lowercase: {len(offenders)}')
        for user in offenders:
            self.stdout.write(f'  {user.pk:6}  {user.username!r}  email={user.email!r}')

        if collisions:
            self.stdout.write('\nLeft alone: the lowercase form belongs to another account.')
            for user in collisions:
                self.stdout.write(f'  {user.pk:6}  {user.username!r}'
                                  f'  collides with an existing {user.username.lower()!r}')

        if not options['apply']:
            self.stdout.write(
                f'\nDry run. {len(fixable)} could be lowercased. '
                f'Re-run with --apply to do it.')
            return

        with transaction.atomic():
            for user in fixable:
                user.username = user.username.lower()
                if user.email:
                    user.email = user.email.lower()
                # save() runs the pre_save hook, which is the same rule this command
                # applies, so the two cannot disagree about what "lowercase" means.
                user.save()
        self.stdout.write(f'\nLowercased {len(fixable)} accounts.')
