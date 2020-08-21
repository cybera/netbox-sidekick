from django.contrib.auth.mixins import PermissionRequiredMixin
from django.shortcuts import get_object_or_404
from django.views.generic import DetailView

from django_filters.views import FilterView
from django_tables2.views import SingleTableView

from netbox_sidekick.filters import (
    LogicalSystemFilterSet, RoutingTypeFilterSet,
    NetworkServiceTypeFilterSet, NetworkServiceFilterSet,
)

from netbox_sidekick.tables import (
    LogicalSystemTable, RoutingTypeTable,
    NetworkServiceTypeTable, NetworkServiceTable,
)

from netbox_sidekick.models import (
    LogicalSystem, NetworkServiceType,
    NetworkService, RoutingType,
)


# Logical System Index
class LogicalSystemIndexView(PermissionRequiredMixin, FilterView, SingleTableView):
    permission_required = 'netbox_sidekick.view_logicalsystem'
    model = LogicalSystem
    table_class = LogicalSystemTable
    filterset_class = LogicalSystemFilterSet
    template_name = 'netbox_sidekick/networkservice/logicalsystem_index.html'


# Logical System Details
class LogicalSystemDetailView(PermissionRequiredMixin, DetailView):
    permission_required = 'netbox_sidekick.view_logicalsystem'
    model = LogicalSystem
    template_name = 'netbox_sidekick/networkservice/logicalsystem.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        logical_system = get_object_or_404(LogicalSystem, slug=self.kwargs['slug'])
        context['logical_system'] = logical_system

        table = NetworkServiceTable(NetworkService.objects.filter(
            logical_system=logical_system.id))
        context['table'] = table

        return context


# Routing Type Index
class RoutingTypeIndexView(PermissionRequiredMixin, FilterView, SingleTableView):
    permission_required = 'netbox_sidekick.view_routingtype'
    model = RoutingType
    table_class = RoutingTypeTable
    filterset_class = RoutingTypeFilterSet
    template_name = 'netbox_sidekick/networkservice/routingtype_index.html'


# Routing Type Details
class RoutingTypeDetailView(PermissionRequiredMixin, DetailView):
    permission_required = 'netbox_sidekick.view_routingtype'
    model = RoutingType
    template_name = 'netbox_sidekick/networkservice/routingtype.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        routing_type = get_object_or_404(RoutingType, slug=self.kwargs['slug'])
        context['routing_type'] = routing_type

        table = NetworkServiceTable(NetworkService.objects.filter(
            routing_type=routing_type.id))
        context['table'] = table

        return context


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
