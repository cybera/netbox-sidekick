from django.contrib.auth.mixins import PermissionRequiredMixin
from django.shortcuts import get_object_or_404
from django.views.generic import DetailView

from django_filters.views import FilterView
from django_tables2.views import SingleTableView

from netbox_sidekick.filters import (
    NICFilterSet,
)

from netbox_sidekick.tables import (
    NICTable,
)

from netbox_sidekick.models import (
    NIC,
)


# NIC Index
class NICIndexView(PermissionRequiredMixin, FilterView, SingleTableView):
    permission_required = 'netbox_sidekick.view_nic'
    model = NIC
    table_class = NICTable
    filterset_class = NICFilterSet
    template_name = 'netbox_sidekick/nic/nic_index.html'


# NIC Details
class NICDetailView(PermissionRequiredMixin, DetailView):
    permission_required = 'netbox_sidekick.view_nic'
    model = NIC
    template_name = 'netbox_sidekick/nic/nic.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        nic = get_object_or_404(NIC, pk=self.kwargs['pk'])
        context['nic'] = nic

        return context
