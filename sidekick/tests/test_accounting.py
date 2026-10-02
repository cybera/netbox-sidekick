from html.parser import HTMLParser

from django.urls import reverse

from sidekick.models import (
    AccountingProfile,
    AccountingSource,
    BandwidthProfile,
)

from .utils import BaseTest


class _FormsetInputParser(HTMLParser):
    """
    Collect the bandwidth-profile formset's inputs from a rendered edit page,
    exactly as a browser would submit them: checked checkboxes only, textarea
    contents included.
    """

    PREFIX = 'bandwidth_profiles-'

    def __init__(self, prefix=None):
        super().__init__()
        if prefix is not None:
            self.PREFIX = prefix
        self.values = {}
        self._textarea = None

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        name = attrs.get('name', '')
        # Capture both the field inputs and the initial-* hidden inputs Django
        # renders for change detection. Omitting the initial-* inputs would
        # itself make every field look changed.
        is_field = name.startswith(self.PREFIX)
        is_initial = name.startswith(f'initial-{self.PREFIX}')
        if not (is_field or is_initial):
            return
        if tag == 'input':
            itype = attrs.get('type', 'text')
            if itype in ('checkbox', 'radio'):
                if 'checked' in attrs:
                    self.values[name] = attrs.get('value', 'on')
            elif itype != 'file':
                self.values[name] = attrs.get('value', '')
        elif tag == 'textarea':
            self._textarea = name
            self.values[name] = ''

    def handle_data(self, data):
        if self._textarea:
            self.values[self._textarea] += data

    def handle_endtag(self, tag):
        if tag == 'textarea':
            self._textarea = None


class AccountingTest(BaseTest):
    # Accounting Source
    def test_accountingsource_basic(self):
        v = AccountingSource.objects.get(device=1, name='Client-EastUniversity')
        self.assertEqual(v.destination, 'Primary ISP')

    def test_view_accountingsource_list(self):
        resp = self.client.get(
            reverse('plugins:sidekick:accountingsource_list'))
        self.assertContains(resp, 'Router 1')
        self.assertContains(resp, 'Router 2')
        self.assertContains(resp, 'Client-EastUniversity')

    def test_view_accountingsource_detail(self):
        v = AccountingSource.objects.get(device=1, name='Client-EastUniversity')
        resp = self.client.get(v.get_absolute_url())
        self.assertContains(resp, 'Client-EastUniversity')
        self.assertContains(resp, 'Primary ISP')

    # Accounting Profile
    def test_accountingprofile_basic(self):
        v = AccountingProfile.objects.get(id=1)
        self.assertEqual(v.comments, "East University's profile")

    def test_view_accountingprofile_list(self):
        resp = self.client.get(
            reverse('plugins:sidekick:accountingprofile_list'))
        self.assertContains(resp, 'East University')

    def test_view_accountingprofile_detail(self):
        v = AccountingProfile.objects.get(id=1)
        resp = self.client.get(v.get_absolute_url())
        # Comments are rendered by the standard CommentsPanel (as markdown).
        self.assertContains(resp, "East University's profile")

        # The bandwidth history table is rendered by an HTMX ObjectsTablePanel,
        # so its rows are not part of the initial page response. Verify the
        # panel is wired to the correctly filtered list endpoint instead.
        self.assertContains(resp, 'accounting_profile_id=1')
        resp = self.client.get(
            reverse('plugins:sidekick:bandwidthprofile_list'),
            {'embedded': 'True', 'accounting_profile_id': 1},
        )
        self.assertContains(resp, '200000000')

    # Bandwidth Profile
    def test_bandwidthprofile_basic(self):
        v = BandwidthProfile.objects.get(id=1)
        self.assertEqual(v.traffic_cap, 200000000)

    def test_view_bandwidthprofile_list(self):
        resp = self.client.get(
            reverse('plugins:sidekick:bandwidthprofile_list'))
        self.assertContains(resp, 'East University')
        self.assertContains(resp, '200000000')


class AccountingProfileInlineTest(BaseTest):
    """
    The Bandwidth Profiles inline on the AccountingProfile edit page.

    This replaces the Django admin's BandwidthProfileInline, which was removed
    with the admin in NetBox 4 (ADR-064). NetBox's generic ObjectEditView has
    no formset support, so the formset is owned by AccountingProfileForm.
    """

    def setUp(self):
        super().setUp()
        self.profile = AccountingProfile.objects.get(pk=1)
        self.url = reverse(
            'plugins:sidekick:accountingprofile_edit', args=[self.profile.pk])

    def post_data(self, rows, **overrides):
        """
        Build a POST body for the edit view: the main profile fields plus the
        bandwidth-profile formset management data and rows.
        """
        data = {
            'member': str(self.profile.member_id),
            'name': self.profile.name or '',
            'enabled': 'on',
            'comments': self.profile.comments or '',
            'accounting_sources': [
                str(pk) for pk in self.profile.accounting_sources.values_list('pk', flat=True)
            ],
        }
        data.update(overrides)

        data['bandwidth_profiles-TOTAL_FORMS'] = str(len(rows))
        data['bandwidth_profiles-INITIAL_FORMS'] = str(
            len([r for r in rows if r.get('id')]))
        data['bandwidth_profiles-MIN_NUM_FORMS'] = '0'
        data['bandwidth_profiles-MAX_NUM_FORMS'] = '1000'

        for i, row in enumerate(rows):
            for key, value in row.items():
                data[f'bandwidth_profiles-{i}-{key}'] = value
        return data

    def test_edit_page_renders_inline(self):
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        # Formset management data and the existing row's fields are present.
        self.assertContains(resp, 'bandwidth_profiles-TOTAL_FORMS')
        self.assertContains(resp, 'bandwidth_profiles-0-traffic_cap')
        self.assertContains(resp, 'bandwidth_profiles-0-billable')
        # The existing row is carried as a hidden pk, so edits target it.
        self.assertContains(resp, 'bandwidth_profiles-0-id')
        self.assertContains(resp, 'Bandwidth Profiles')

    def test_inline_adds_bandwidth_profile(self):
        rows = [
            {'id': '1', 'effective_date': '2021-05-27', 'traffic_cap': '200000000',
             'burst_limit': '2000000', 'billable': 'on', 'comments': ''},
            {'effective_date': '2026-01-01', 'traffic_cap': '350', 'burst_limit': '4',
             'billable': 'on', 'comments': 'raised per request'},
        ]
        resp = self.client.post(self.url, self.post_data(rows))
        self.assertEqual(resp.status_code, 302)

        new = BandwidthProfile.objects.get(effective_date='2026-01-01')
        self.assertEqual(new.accounting_profile_id, self.profile.pk)
        self.assertEqual(new.traffic_cap, 350)
        self.assertEqual(new.burst_limit, 4)
        self.assertTrue(new.billable)

    def test_inline_edits_bandwidth_profile(self):
        rows = [
            {'id': '1', 'effective_date': '2021-05-27', 'traffic_cap': '999',
             'burst_limit': '2000000', 'billable': 'on', 'comments': 'corrected'},
        ]
        resp = self.client.post(self.url, self.post_data(rows))
        self.assertEqual(resp.status_code, 302)

        self.profile.refresh_from_db()
        updated = BandwidthProfile.objects.get(pk=1)
        self.assertEqual(updated.traffic_cap, 999)
        self.assertEqual(updated.comments, 'corrected')
        # An edit must not create a duplicate row.
        self.assertEqual(self.profile.bandwidthprofile_set.count(), 1)

    def test_inline_deletes_bandwidth_profile(self):
        rows = [
            {'id': '1', 'effective_date': '2021-05-27', 'traffic_cap': '200000000',
             'burst_limit': '2000000', 'billable': 'on', 'comments': '',
             'DELETE': 'on'},
        ]
        resp = self.client.post(self.url, self.post_data(rows))
        self.assertEqual(resp.status_code, 302)
        self.assertFalse(BandwidthProfile.objects.filter(pk=1).exists())

    def test_submitting_the_rendered_page_unchanged_creates_nothing(self):
        """
        Regression test for a phantom-row bug.

        The blank row's effective_date is pre-filled from the model default.
        While that default was timezone.now() -- a datetime on a DateField --
        Django rendered it into the initial-* hidden input as
        "YYYY-MM-DD HH:MM:SS+00:00", which DateField.to_python() cannot parse.
        BoundField._has_changed() then took its "assume changed" branch, so the
        blank row was always considered changed and every save of the profile
        created an empty BandwidthProfile.

        The earlier test posted an empty date, which masked the bug. This one
        submits the form exactly as the page renders it.
        """
        html = self.client.get(self.url).content.decode()
        parser = _FormsetInputParser()
        parser.feed(html)
        formset_data = parser.values

        # Sanity: the page really did render a blank row with a pre-filled date.
        blank = formset_data['bandwidth_profiles-INITIAL_FORMS']
        self.assertIn(f'bandwidth_profiles-{blank}-effective_date', formset_data)

        data = self.post_data([])
        data.pop('bandwidth_profiles-TOTAL_FORMS')
        data.update(formset_data)

        resp = self.client.post(self.url, data)
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(
            self.profile.bandwidthprofile_set.count(), 1,
            'saving the profile untouched must not create a bandwidth profile',
        )

    def test_untouched_blank_row_creates_nothing(self):
        # The edit page always shows one blank row. Submitting the form without
        # touching it (e.g. to rename the profile) must not silently create a
        # phantom BandwidthProfile.
        #
        # Post the blank row exactly as an untouched browser form would:
        # billable is rendered checked (the model default is True), so it comes
        # back as "on" and matches its initial value. Django compares each
        # field against its initial value and skips an unchanged row.
        rows = [
            {'id': '1', 'effective_date': '2021-05-27', 'traffic_cap': '200000000',
             'burst_limit': '2000000', 'billable': 'on', 'comments': ''},
            {'effective_date': '', 'traffic_cap': '', 'burst_limit': '',
             'billable': 'on', 'comments': ''},
        ]
        resp = self.client.post(self.url, self.post_data(rows))
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(self.profile.bandwidthprofile_set.count(), 1)

    def test_invalid_inline_row_blocks_the_whole_save(self):
        rows = [
            {'id': '1', 'effective_date': '2021-05-27', 'traffic_cap': '200000000',
             'burst_limit': '2000000', 'billable': 'on', 'comments': ''},
            # Not an integer: the formset must reject it.
            {'effective_date': '2026-01-01', 'traffic_cap': 'not-a-number',
             'burst_limit': '4', 'billable': 'on', 'comments': ''},
        ]
        resp = self.client.post(self.url, self.post_data(rows))
        # Re-rendered, not redirected.
        self.assertEqual(resp.status_code, 200)
        # Nothing was written: the bad row is rejected and the good row is not
        # saved either, because the whole form is invalid.
        self.assertFalse(
            BandwidthProfile.objects.filter(effective_date='2026-01-01').exists())
        self.assertEqual(self.profile.bandwidthprofile_set.count(), 1)
        self.assertEqual(
            BandwidthProfile.objects.get(pk=1).traffic_cap, 200000000)

    def test_inline_on_add_page_creates_row_with_new_profile(self):
        url = reverse('plugins:sidekick:accountingprofile_add')
        data = {
            'member': '2',
            'name': 'New Profile',
            'enabled': 'on',
            'comments': '',
            'accounting_sources': [],
            'bandwidth_profiles-TOTAL_FORMS': '1',
            'bandwidth_profiles-INITIAL_FORMS': '0',
            'bandwidth_profiles-MIN_NUM_FORMS': '0',
            'bandwidth_profiles-MAX_NUM_FORMS': '1000',
            'bandwidth_profiles-0-effective_date': '2026-02-01',
            'bandwidth_profiles-0-traffic_cap': '500',
            'bandwidth_profiles-0-burst_limit': '5',
            'bandwidth_profiles-0-billable': 'on',
            'bandwidth_profiles-0-comments': '',
        }
        resp = self.client.post(url, data)
        self.assertEqual(resp.status_code, 302)

        created = AccountingProfile.objects.get(name='New Profile')
        row = created.bandwidthprofile_set.get()
        self.assertEqual(row.traffic_cap, 500)
        self.assertEqual(str(row.effective_date), '2026-02-01')


class BandwidthProfileFormTest(BaseTest):
    def test_standalone_form_exposes_billable(self):
        # billable is a model field and was exposed by the removed admin inline,
        # but was missing from the plugin's standalone form.
        from sidekick.forms import BandwidthProfileForm
        self.assertIn('billable', BandwidthProfileForm().fields)
