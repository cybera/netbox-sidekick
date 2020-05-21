from io import StringIO
from django.core.management import call_command

import os

from . import utils


class ImportMemberTest(utils.BaseTest):
    def test_reconcile(self):
        dir_path = os.path.dirname(os.path.realpath(__file__))
        csv = f"{dir_path}/../fixtures/members.csv"

        out = StringIO()
        call_command('import_members', stdout=out, file=csv, reconcile=True)
        self.assertIn('Tenant not found: West School District', out.getvalue())
        self.assertIn('Member not found: Central School', out.getvalue())

    def test_dry_run(self):
        dir_path = os.path.dirname(os.path.realpath(__file__))
        csv = f"{dir_path}/../fixtures/members.csv"

        out = StringIO()
        call_command('import_members', stdout=out, file=csv, dry_run=True)

        self.assertIn('WARNING: No tenant found for West School District. Skipping.', out.getvalue())
        self.assertIn('Would have created Member Type: Government/Not For Profit', out.getvalue())
        self.assertIn('Would have created Member: South Not For Profit', out.getvalue())

    def test_import(self):
        dir_path = os.path.dirname(os.path.realpath(__file__))
        csv = f"{dir_path}/../fixtures/members.csv"

        out = StringIO()
        call_command('import_members', stdout=out, file=csv)

        self.assertIn('WARNING: No tenant found for West School District. Skipping.', out.getvalue())
        self.assertIn('Created Member Type: Government/Not For Profit', out.getvalue())
        self.assertIn('Created Member: South Not For Profit', out.getvalue())
