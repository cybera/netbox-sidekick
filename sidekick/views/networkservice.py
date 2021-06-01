from django.conf import settings
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.shortcuts import get_object_or_404
from django.views.generic import DetailView

from django_filters.views import FilterView
from django_tables2.views import SingleTableView

from sidekick.filters import (
    LogicalSystemFilterSet, RoutingTypeFilterSet,
    NetworkServiceTypeFilterSet, NetworkServiceFilterSet,
    NetworkServiceGroupFilterSet,
)

from sidekick.tables import (
    LogicalSystemTable, RoutingTypeTable,
    NetworkServiceTypeTable, NetworkServiceTable,
    NetworkServiceGroupTable,
)

from sidekick.models import (
    LogicalSystem, RoutingType,
    NetworkServiceType,
    NetworkService,
    NetworkServiceGroup,
)

from sidekick.utils import (
    get_graphite_service_graph
)


# Logical System Index
class LogicalSystemIndexView(PermissionRequiredMixin, FilterView, SingleTableView):
    permission_required = 'sidekick.view_logicalsystem'
    model = LogicalSystem
    table_class = LogicalSystemTable
    filterset_class = LogicalSystemFilterSet
    template_name = 'sidekick/networkservice/logicalsystem_index.html'


# Logical System Details
class LogicalSystemDetailView(PermissionRequiredMixin, DetailView):
    permission_required = 'sidekick.view_logicalsystem'
    model = LogicalSystem
    template_name = 'sidekick/networkservice/logicalsystem.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        logical_system = get_object_or_404(LogicalSystem, slug=self.kwargs['slug'])
        context['logical_system'] = logical_system

        table = NetworkServiceTable(NetworkService.objects.filter(
            network_service_devices__network_service_l3__logical_system=logical_system.id))
        context['table'] = table

        return context


# Routing Type Index
class RoutingTypeIndexView(PermissionRequiredMixin, FilterView, SingleTableView):
    permission_required = 'sidekick.view_routingtype'
    model = RoutingType
    table_class = RoutingTypeTable
    filterset_class = RoutingTypeFilterSet
    template_name = 'sidekick/networkservice/routingtype_index.html'


# Routing Type Details
class RoutingTypeDetailView(PermissionRequiredMixin, DetailView):
    permission_required = 'sidekick.view_routingtype'
    model = RoutingType
    template_name = 'sidekick/networkservice/routingtype.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        routing_type = get_object_or_404(RoutingType, slug=self.kwargs['slug'])
        context['routing_type'] = routing_type

        table = NetworkServiceTable(NetworkService.objects.filter(
            network_service_devices__network_service_l3__routing_type=routing_type.id))
        context['table'] = table

        return context


# Network Service Type Index
class NetworkServiceTypeIndexView(PermissionRequiredMixin, FilterView, SingleTableView):
    permission_required = 'sidekick.view_networkservicetype'
    model = NetworkServiceType
    table_class = NetworkServiceTypeTable
    filterset_class = NetworkServiceTypeFilterSet
    template_name = 'sidekick/networkservice/networkservicetype_index.html'


# Network Service Type Details
class NetworkServiceTypeDetailView(PermissionRequiredMixin, DetailView):
    permission_required = 'sidekick.view_networkservicetype'
    model = NetworkServiceType
    template_name = 'sidekick/networkservice/networkservicetype.html'

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
    permission_required = 'sidekick.view_networkservice'
    model = NetworkService
    table_class = NetworkServiceTable
    filterset_class = NetworkServiceFilterSet
    template_name = 'sidekick/networkservice/networkservice_index.html'


# Network Service Details
class NetworkServiceDetailView(PermissionRequiredMixin, DetailView):
    permission_required = 'sidekick.view_networkservice'
    model = NetworkService
    context_object_name = 'ns'
    template_name = 'sidekick/networkservice/networkservice.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        ns = NetworkService.objects.get(pk=self.kwargs['pk'])

        graphite_render_host = settings.PLUGINS_CONFIG['sidekick'].get('graphite_render_host', None)
        graph_data = get_graphite_service_graph(ns, graphite_render_host)
        context['graph_data'] = graph_data

        return context


# Network Service Group Index
class NetworkServiceGroupIndexView(PermissionRequiredMixin, FilterView, SingleTableView):
    permission_required = 'sidekick.view_networkservicegroup'
    model = NetworkServiceGroup
    table_class = NetworkServiceGroupTable
    filterset_class = NetworkServiceGroupFilterSet
    template_name = 'sidekick/networkservice/networkservicegroup_index.html'


# Network Service Group Details
class NetworkServiceGroupDetailView(PermissionRequiredMixin, DetailView):
    permission_required = 'sidekick.view_networkservicegroup'
    model = NetworkServiceGroup
    context_object_name = 'nsg'
    template_name = 'sidekick/networkservice/networkservicegroup.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        nsg = get_object_or_404(NetworkServiceGroup, pk=self.kwargs['pk'])
        context['nsg'] = nsg

        table = NetworkServiceTable(NetworkService.objects.filter(
            pk__in=nsg.network_services.all()))
        context['table'] = table

        return context
