from django.contrib.auth.mixins import PermissionRequiredMixin
from django.shortcuts import get_object_or_404
from django.views.generic import DetailView

from django_filters.views import FilterView
from django_tables2.views import SingleTableView

from netbox_sidekick.filters import NetworkServiceTypeFilterSet, NetworkServiceFilterSet
from netbox_sidekick.models import NetworkServiceType, NetworkService
from netbox_sidekick.tables import NetworkServiceTypeTable, NetworkServiceTable


# Network Service Type Index
class NetworkServiceTypeIndexView(PermissionRequiredMixin, FilterView, SingleTableView):
    permission_required = 'netbox_sidekick.view_networkservicetype'
    model = NetworkServiceType
    table_class = NetworkServiceTypeTable
    filterset_class = NetworkServiceTypeFilterSet
    template_name = 'netbox_sidekick/networkservice/networkservicetype_index.html'


# Network Service Type Details
class NetworkServiceTypeDetailView(PermissionRequiredMixin, DetailView):
    permission_required = 'netbox_sidekick.view_networkservicetype'
    model = NetworkServiceType
    template_name = 'netbox_sidekick/networkservice/networkservicetype.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        nst = get_object_or_404(NetworkServiceType, slug=self.kwargs['slug'])
        context['nst'] = nst

        table = NetworkServiceTable(NetworkService.objects.filter(
            network_service_type=nst.id))
        context['table'] = table

        return context


# Network Service Index
class NetworkServiceIndexView(PermissionRequiredMixin, FilterView, SingleTableView):
    permission_required = 'netbox_sidekick.view_networkservice'
    model = NetworkService
    table_class = NetworkServiceTable
    filterset_class = NetworkServiceFilterSet
    template_name = 'netbox_sidekick/networkservice/networkservice_index.html'


# Network Service Details
class NetworkServiceDetailView(PermissionRequiredMixin, DetailView):
    permission_required = 'netbox_sidekick.view_networkservice'
    model = NetworkService
    context_object_name = 'ns'
    template_name = 'netbox_sidekick/networkservice/networkservice.html'
