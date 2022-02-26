from io import StringIO
from django.core.management import call_command

import os

from . import utils


class ImportMemberTest(utils.BaseTest):
    def test_dry_run(self):
        dir_path = os.path.dirname(os.path.realpath(__file__))
        csv = f"{dir_path}/../fixtures/members.csv"

        out = StringIO()
        call_command('import_members', stdout=out, file=csv, dry_run=True)

        self.assertIn('Would have created Tenant: West School District', out.getvalue())
        self.assertIn('Changing description of East University to A description', out.getvalue())
        self.assertIn('Changing comments of East University to Some Comment', out.getvalue())
        self.assertIn('Changing member_type of East University to Post-Secondary Institution', out.getvalue())
        self.assertIn('Changing description of South Not For Profit to A description', out.getvalue())
        self.assertIn('Changing comments of South Not For Profit to A Comment', out.getvalue())
        self.assertIn('Changing member_type of South Not For Profit to Government/Not For Profit', out.getvalue())
        self.assertIn('Changing latitude of Site East University to 3.5', out.getvalue())
        self.assertIn('Changing longitude of Site East University to -13.0', out.getvalue())
        self.assertIn('Changing latitude of Site South Not For Profit to 2.5', out.getvalue())
        self.assertIn('Changing longitude of Site South Not For Profit to -15.0', out.getvalue())

    def test_import(self):
        dir_path = os.path.dirname(os.path.realpath(__file__))
        csv = f"{dir_path}/../fixtures/members.csv"

        out = StringIO()
        call_command('import_members', stdout=out, file=csv)

        self.assertIn('Created Tenant: West School District', out.getvalue())
        self.assertIn('Updated Tenant: South Not For Profit', out.getvalue())
