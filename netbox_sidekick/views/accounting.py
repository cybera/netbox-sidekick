from django.contrib.auth.mixins import PermissionRequiredMixin
from django.shortcuts import get_object_or_404
from django.views.generic import DetailView

from django_filters.views import FilterView
from django_tables2.views import SingleTableView

from netbox_sidekick.filters import (
    BandwidthProfileFilterSet,
    AccountingProfileFilterSet,
    AccountingClassFilterSet,
)

from netbox_sidekick.tables import (
    BandwidthProfileTable,
    AccountingProfileTable,
    AccountingClassTable,
)

from netbox_sidekick.models import (
    BandwidthProfile,
    AccountingProfile,
    AccountingClass,
)


class AccountingClassIndexView(PermissionRequiredMixin, FilterView, SingleTableView):
    permission_required = 'netbox_sidekick.view_accountingclass'
    model = AccountingClass
    table_class = AccountingClassTable
    filterset_class = AccountingClassFilterSet
    template_name = 'netbox_sidekick/accounting/accountingclass_index.html'


class AccountingClassDetailView(PermissionRequiredMixin, DetailView):
    permission_required = 'netbox_sidekick.view_accountingclass'
    model = AccountingClass
    template_name = 'netbox_sidekick/accounting/accountingclass.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        accounting_class = get_object_or_404(AccountingClass, pk=self.kwargs['pk'])
        context['accounting_class'] = accounting_class

        table = AccountingProfileTable(AccountingProfile.objects.filter(
            accounting_classes__in=[accounting_class.id]))
        context['table'] = table

        return context


class AccountingProfileIndexView(PermissionRequiredMixin, FilterView, SingleTableView):
    permission_required = 'netbox_sidekick.view_accountingprofile'
    model = AccountingProfile
    table_class = AccountingProfileTable
    filterset_class = AccountingProfileFilterSet
    template_name = 'netbox_sidekick/accounting/accountingprofile_index.html'


class AccountingProfileDetailView(PermissionRequiredMixin, DetailView):
    permission_required = 'netbox_sidekick.view_accountingprofile'
    model = AccountingProfile
    template_name = 'netbox_sidekick/accounting/accountingprofile.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        accounting_profile = get_object_or_404(AccountingProfile, pk=self.kwargs['pk'])
        context['accounting_profile'] = accounting_profile

        return context


class BandwidthProfileIndexView(PermissionRequiredMixin, FilterView, SingleTableView):
    permission_required = 'netbox_sidekick.view_bandwidthprofile'
    model = BandwidthProfile
    table_class = BandwidthProfileTable
    filterset_class = BandwidthProfileFilterSet
    template_name = 'netbox_sidekick/accounting/bandwidthprofile_index.html'


class BandwidthProfileDetailView(PermissionRequiredMixin, DetailView):
    permission_required = 'netbox_sidekick.view_bandwidthprofile'
    model = BandwidthProfile
    template_name = 'netbox_sidekick/accounting/bandwidthprofile.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        bandwidth_profile = get_object_or_404(BandwidthProfile, pk=self.kwargs['pk'])
        context['bandwidth_profile'] = bandwidth_profile

        return context
