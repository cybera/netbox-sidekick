from io import StringIO
from django.core.management import call_command

import os

from . import utils


class ImportInstitutionsTest(utils.BaseTest):
    def test_dry_run(self):
        dir_path = os.path.dirname(os.path.realpath(__file__))
        csv = f"{dir_path}/../fixtures/institutions.csv"

        out = StringIO()
        call_command('import_institutions', stdout=out, file=csv, dry_run=True)

        self.assertIn('WARNING: No tenant found for Does Not Exist. Skipping.', out.getvalue())
        self.assertIn('Would have updated East University', out.getvalue())
        self.assertIn('Would have updated Central School', out.getvalue())

    def test_import(self):
        dir_path = os.path.dirname(os.path.realpath(__file__))
        csv = f"{dir_path}/../fixtures/institutions.csv"

        out = StringIO()
        call_command('import_institutions', stdout=out, file=csv)
        self.assertIn('WARNING: No tenant found for Does Not Exist. Skipping.', out.getvalue())
        self.assertIn('Updated East University', out.getvalue())
        self.assertIn('Updated Central School', out.getvalue())
