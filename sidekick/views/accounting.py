from netbox.views.generic import (
    ObjectView, ObjectListView,
    ObjectEditView, ObjectDeleteView,
)

from sidekick.forms import (
    AccountingProfileForm,
    BandwidthProfileForm
)

from sidekick.filters import (
    BandwidthProfileFilterSet,
    BandwidthProfileFilterSetForm,
    AccountingProfileFilterSet,
    AccountingProfileFilterSetForm,
    AccountingSourceFilterSet,
    AccountingSourceFilterSetForm,
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


class AccountingSourceIndexView(ObjectListView):
    queryset = AccountingSource.objects.all()
    model = AccountingSource
    table = AccountingSourceTable
    filterset = AccountingSourceFilterSet
    filterset_form = AccountingSourceFilterSetForm


class AccountingSourceDetailView(ObjectView):
    queryset = AccountingSource.objects.all()

    def get_extra_context(self, request, instance):
        table = AccountingProfileTable(AccountingProfile.objects.filter(
            accounting_sources__id__in=[instance.id]))

        return {
            'accountingprofile_table': table,
        }


class AccountingProfileIndexView(ObjectListView):
    queryset = AccountingProfile.objects.all()
    model = AccountingProfile
    table = AccountingProfileTable
    filterset = AccountingProfileFilterSet
    filterset_form = AccountingProfileFilterSetForm


class AccountingProfileDetailView(ObjectView):
    queryset = AccountingProfile.objects.all()


class AccountingProfileEditView(ObjectEditView):
    queryset = AccountingProfile.objects.all()
    form = AccountingProfileForm


class AccountingProfileDeleteView(ObjectDeleteView):
    queryset = AccountingProfile.objects.all()


class BandwidthProfileIndexView(ObjectListView):
    queryset = BandwidthProfile.objects.all()
    model = BandwidthProfile
    table = BandwidthProfileTable
    filterset = BandwidthProfileFilterSet
    filterset_form = BandwidthProfileFilterSetForm


class BandwidthProfileDetailView(ObjectView):
    queryset = BandwidthProfile.objects.all()


class BandwidthProfileEditView(ObjectEditView):
    queryset = BandwidthProfile.objects.all()
    form = BandwidthProfileForm


class BandwidthProfileDeleteView(ObjectDeleteView):
    queryset = BandwidthProfile.objects.all()
