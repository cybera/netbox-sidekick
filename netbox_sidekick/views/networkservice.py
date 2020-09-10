from django.contrib.auth.mixins import PermissionRequiredMixin
from django.shortcuts import get_object_or_404
from django.views.generic import DetailView

from django_filters.views import FilterView
from django_tables2.views import SingleTableView

from netbox_sidekick.filters import (
    LogicalSystemFilterSet, RoutingTypeFilterSet,
    NetworkServiceConnectionTypeFilterSet, NetworkServiceConnectionFilterSet,
)

from netbox_sidekick.tables import (
    LogicalSystemTable, RoutingTypeTable,
    NetworkServiceConnectionTypeTable, NetworkServiceConnectionTable,
)

from netbox_sidekick.models import (
    LogicalSystem, RoutingType,
    NetworkServiceConnectionType, NetworkServiceConnection,
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

        table = NetworkServiceConnectionTable(NetworkServiceConnection.objects.filter(
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

        table = NetworkServiceConnectionTable(NetworkServiceConnection.objects.filter(
            routing_type=routing_type.id))
        context['table'] = table

        return context


# Network Service Connection Type Index
class NetworkServiceConnectionTypeIndexView(PermissionRequiredMixin, FilterView, SingleTableView):
    permission_required = 'netbox_sidekick.view_networkserviceconnectiontype'
    model = NetworkServiceConnectionType
    table_class = NetworkServiceConnectionTypeTable
    filterset_class = NetworkServiceConnectionTypeFilterSet
    template_name = 'netbox_sidekick/networkservice/networkserviceconnectiontype_index.html'


# Network Service Connection Type Details
class NetworkServiceConnectionTypeDetailView(PermissionRequiredMixin, DetailView):
    permission_required = 'netbox_sidekick.view_networkserviceconnectiontype'
    model = NetworkServiceConnectionType
    template_name = 'netbox_sidekick/networkservice/networkserviceconnectiontype.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        nst = get_object_or_404(NetworkServiceConnectionType, slug=self.kwargs['slug'])
        context['nst'] = nst

        table = NetworkServiceConnectionTable(NetworkServiceConnection.objects.filter(
            network_service_connection_type=nst.id))
        context['table'] = table

        return context


# Network Service Connection Index
class NetworkServiceConnectionIndexView(PermissionRequiredMixin, FilterView, SingleTableView):
    permission_required = 'netbox_sidekick.view_networkserviceconnection'
    model = NetworkServiceConnection
    table_class = NetworkServiceConnectionTable
    filterset_class = NetworkServiceConnectionFilterSet
    template_name = 'netbox_sidekick/networkservice/networkserviceconnection_index.html'


# Network Service Connection Details
class NetworkServiceConnectionDetailView(PermissionRequiredMixin, DetailView):
    permission_required = 'netbox_sidekick.view_networkserviceconnection'
    model = NetworkServiceConnection
    context_object_name = 'ns'
    template_name = 'netbox_sidekick/networkservice/networkserviceconnection.html'
