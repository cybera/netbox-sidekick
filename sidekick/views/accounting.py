from netbox.views import generic
from utilities.views import register_model_view

from sidekick import filtersets, forms, tables
from sidekick.models import (
    AccountingProfile,
    AccountingSource,
    BandwidthProfile,
)
from sidekick.ui import panels

from .base import SidekickObjectView


#
# Accounting sources
#

@register_model_view(AccountingSource, 'list', path='', detail=False)
class AccountingSourceListView(generic.ObjectListView):
    queryset = AccountingSource.objects.all()
    table = tables.AccountingSourceTable
    filterset = filtersets.AccountingSourceFilterSet
    filterset_form = filtersets.AccountingSourceFilterSetForm


@register_model_view(AccountingSource)
class AccountingSourceView(SidekickObjectView):
    queryset = AccountingSource.objects.all()
    layout = panels.ACCOUNTING_SOURCE_LAYOUT


@register_model_view(AccountingSource, 'add', detail=False)
@register_model_view(AccountingSource, 'edit')
class AccountingSourceEditView(generic.ObjectEditView):
    queryset = AccountingSource.objects.all()
    form = forms.AccountingSourceForm


@register_model_view(AccountingSource, 'delete')
class AccountingSourceDeleteView(generic.ObjectDeleteView):
    queryset = AccountingSource.objects.all()


#
# Accounting profiles
#

@register_model_view(AccountingProfile, 'list', path='', detail=False)
class AccountingProfileListView(generic.ObjectListView):
    queryset = AccountingProfile.objects.all()
    table = tables.AccountingProfileTable
    filterset = filtersets.AccountingProfileFilterSet
    filterset_form = filtersets.AccountingProfileFilterSetForm


@register_model_view(AccountingProfile)
class AccountingProfileView(SidekickObjectView):
    queryset = AccountingProfile.objects.all()
    layout = panels.ACCOUNTING_PROFILE_LAYOUT


@register_model_view(AccountingProfile, 'add', detail=False)
@register_model_view(AccountingProfile, 'edit')
class AccountingProfileEditView(generic.ObjectEditView):
    queryset = AccountingProfile.objects.all()
    form = forms.AccountingProfileForm


@register_model_view(AccountingProfile, 'delete')
class AccountingProfileDeleteView(generic.ObjectDeleteView):
    queryset = AccountingProfile.objects.all()


#
# Bandwidth profiles
#

@register_model_view(BandwidthProfile, 'list', path='', detail=False)
class BandwidthProfileListView(generic.ObjectListView):
    queryset = BandwidthProfile.objects.all()
    table = tables.BandwidthProfileTable
    filterset = filtersets.BandwidthProfileFilterSet
    filterset_form = filtersets.BandwidthProfileFilterSetForm


@register_model_view(BandwidthProfile)
class BandwidthProfileView(SidekickObjectView):
    queryset = BandwidthProfile.objects.all()
    layout = panels.BANDWIDTH_PROFILE_LAYOUT


@register_model_view(BandwidthProfile, 'add', detail=False)
@register_model_view(BandwidthProfile, 'edit')
class BandwidthProfileEditView(generic.ObjectEditView):
    queryset = BandwidthProfile.objects.all()
    form = forms.BandwidthProfileForm


@register_model_view(BandwidthProfile, 'delete')
class BandwidthProfileDeleteView(generic.ObjectDeleteView):
    queryset = BandwidthProfile.objects.all()
