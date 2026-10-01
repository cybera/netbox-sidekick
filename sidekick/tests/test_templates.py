"""Regression guards for the graph templates.

NetBox 4.x does not ship jQuery on its UI pages -- the only copy in the tree
belongs to the DRF browsable API.  The first-class rewrite removed the
``<script src="https://code.jquery.com/...">`` tags that the old templates
loaded, but left every ``$()`` call site behind, so all four graph surfaces
raised ``ReferenceError: $ is not defined`` and rendered nothing at all.

These tests scan the templates themselves rather than rendering pages, so they
cover every graph surface, including ones with no fixture coverage.
"""
import re
from pathlib import Path

from .utils import BaseTest

TEMPLATE_DIR = Path(__file__).resolve().parent.parent / 'templates'

# jQuery call syntax: $(...), $.ajax, $(document).ready
JQUERY_CALL = re.compile(r'\$[.(]')

CDN_HOSTS = ('code.jquery.com', 'leeoniya.github.io')


def _strip_django_comments(text):
    """Remove {# ... #} so explanatory comments don't trip the scans."""
    return re.sub(r'\{#.*?#\}', '', text, flags=re.S)


def _template_files():
    return sorted(TEMPLATE_DIR.rglob('*.html'))


def _location(path, lineno):
    return path.name + ':' + str(lineno)


class TemplateDependencyTest(BaseTest):

    def test_no_template_calls_jquery(self):
        offenders = []
        for path in _template_files():
            text = _strip_django_comments(path.read_text())
            for lineno, line in enumerate(text.splitlines(), 1):
                if line.strip().startswith('//'):
                    continue
                if JQUERY_CALL.search(line):
                    offenders.append(_location(path, lineno) + ': ' + line.strip())
        message = 'jQuery call sites found; NetBox 4.x provides no jQuery:'
        self.assertEqual(offenders, [], message + '\n' + '\n'.join(offenders))

    def test_no_template_references_a_cdn(self):
        offenders = []
        for path in _template_files():
            text = _strip_django_comments(path.read_text())
            for lineno, line in enumerate(text.splitlines(), 1):
                for host in CDN_HOSTS:
                    if host in line:
                        offenders.append(_location(path, lineno) + ': ' + host)
        message = 'CDN references found; these assets must be vendored:'
        self.assertEqual(offenders, [], message + '\n' + '\n'.join(offenders))

    def test_vendored_uplot_asset_exists(self):
        # The path the templates point at must exist in the tree, or every
        # graph silently 404s.
        asset = TEMPLATE_DIR.parent / 'static/sidekick/uplot/uPlot.iife.min.js'
        self.assertTrue(asset.exists(), 'missing vendored asset: ' + str(asset))
        self.assertGreater(asset.stat().st_size, 10000)
