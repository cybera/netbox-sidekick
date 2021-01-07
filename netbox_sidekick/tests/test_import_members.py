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
        self.assertIn('Would have updated Tenant: East University', out.getvalue())
        self.assertIn('Would have updated Tenant: South Not For Profit', out.getvalue())

    def test_import(self):
        dir_path = os.path.dirname(os.path.realpath(__file__))
        csv = f"{dir_path}/../fixtures/members.csv"

        out = StringIO()
        call_command('import_members', stdout=out, file=csv)

        self.assertIn('Created Tenant: West School District', out.getvalue())
        self.assertIn('Updated Tenant: South Not For Profit', out.getvalue())
