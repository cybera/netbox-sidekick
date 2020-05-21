from io import StringIO
from django.core.management import call_command

import os

from . import utils


class ImportMemberNodeLinkTest(utils.BaseTest):
    def test_dry_run(self):
        dir_path = os.path.dirname(os.path.realpath(__file__))
        csv = f"{dir_path}/../fixtures/membernodelinks.csv"

        out = StringIO()
        call_command('import_member_node_links', stdout=out, file=csv, dry_run=True)

        self.assertIn('Would have created Member Node Link: Some NREN Calgary to Some NREN Lethbridge', out.getvalue())

    def test_import(self):
        dir_path = os.path.dirname(os.path.realpath(__file__))
        csv = f"{dir_path}/../fixtures/membernodelinks.csv"

        out = StringIO()
        call_command('import_member_node_links', stdout=out, file=csv)

        self.assertIn('Created Member Node Link: Some NREN Calgary to Some NREN Lethbridge', out.getvalue())
