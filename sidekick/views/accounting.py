from django.contrib.auth.mixins import PermissionRequiredMixin
from django.shortcuts import get_object_or_404
from django.views.generic import DetailView

from django_filters.views import FilterView
from django_tables2.views import SingleTableView

from sidekick.filters import (
    BandwidthProfileFilterSet,
    AccountingProfileFilterSet,
    AccountingSourceFilterSet,
)

from sidekick.tables import (
    BandwidthProfileTable,
    AccountingProfileTable,
    AccountingSourceTable,
)

from sidekick.models import (
    BandwidthProfile,
    AccountingProfile,
    AccountingSource,
)


class AccountingSourceIndexView(PermissionRequiredMixin, FilterView, SingleTableView):
    permission_required = 'sidekick.view_accountingsource'
    model = AccountingSource
    table_class = AccountingSourceTable
    filterset_class = AccountingSourceFilterSet
    template_name = 'sidekick/accounting/accountingsource_index.html'


class AccountingSourceDetailView(PermissionRequiredMixin, DetailView):
    permission_required = 'sidekick.view_accountingsource'
    model = AccountingSource
    template_name = 'sidekick/accounting/accountingsource.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        accounting_source = get_object_or_404(AccountingSource, pk=self.kwargs['pk'])
        context['accounting_source'] = accounting_source

        table = AccountingProfileTable(AccountingProfile.objects.filter(
            accounting_sources__id__in=[accounting_source.id]))
        context['table'] = table

        return context


class AccountingProfileIndexView(PermissionRequiredMixin, FilterView, SingleTableView):
    permission_required = 'sidekick.view_accountingprofile'
    model = AccountingProfile
    table_class = AccountingProfileTable
    filterset_class = AccountingProfileFilterSet
    template_name = 'sidekick/accounting/accountingprofile_index.html'


class AccountingProfileDetailView(PermissionRequiredMixin, DetailView):
    permission_required = 'sidekick.view_accountingprofile'
    model = AccountingProfile
    template_name = 'sidekick/accounting/accountingprofile.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        accounting_profile = get_object_or_404(AccountingProfile, pk=self.kwargs['pk'])
        context['accounting_profile'] = accounting_profile

        return context


class BandwidthProfileIndexView(PermissionRequiredMixin, FilterView, SingleTableView):
    permission_required = 'sidekick.view_bandwidthprofile'
    model = BandwidthProfile
    table_class = BandwidthProfileTable
    filterset_class = BandwidthProfileFilterSet
    template_name = 'sidekick/accounting/bandwidthprofile_index.html'


class BandwidthProfileDetailView(PermissionRequiredMixin, DetailView):
    permission_required = 'sidekick.view_bandwidthprofile'
    model = BandwidthProfile
    template_name = 'sidekick/accounting/bandwidthprofile.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        bandwidth_profile = get_object_or_404(BandwidthProfile, pk=self.kwargs['pk'])
        context['bandwidth_profile'] = bandwidth_profile

        return context
