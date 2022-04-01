from django.conf import settings
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views import View
from django.views.generic import DetailView

from django_filters.views import FilterView
from django_tables2.views import SingleTableView

from sidekick.filters import (
    LogicalSystemFilterSet, RoutingTypeFilterSet,
    NetworkServiceTypeFilterSet, NetworkServiceFilterSet,
    NetworkServiceGroupFilterSet,
)

from sidekick.tables import (
    IPPrefixTable,
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
    get_accounting_sources,
    get_all_ip_prefixes,
    get_graphite_accounting_data,
    get_graphite_remaining_data,
    get_graphite_service_data,
    get_graphite_service_graph,
    get_period,
    get_services,
)


# IP Prefix Index
class IPPrefixIndexView(PermissionRequiredMixin, SingleTableView):
    permission_required = 'sidekick.view_ipprefix'
    model = NetworkService
    context_object_name = 'ns'
    template_name = 'sidekick/networkservice/ipprefix_index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        prefixes = []
        for member_id, data in get_all_ip_prefixes().items():
            for prefix in data['prefixes']:
                prefixes.append({
                    'prefix': prefix,
                    'member': data['member'],
                })
        table = IPPrefixTable(prefixes)
        context['table'] = table

        return context


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


# Network Service graphite data
class NetworkServiceGraphiteDataView(PermissionRequiredMixin, View):
    permission_required = 'sidekick.view_service'
    model = NetworkService

    def get(self, request, pk):
        graphite_render_host = settings.PLUGINS_CONFIG['sidekick'].get('graphite_render_host', None)
        if graphite_render_host is None:
            return JsonResponse({})

        ns = NetworkService.objects.get(pk=self.kwargs['pk'])
        graph_data = get_graphite_service_graph(ns, graphite_render_host)
        return JsonResponse({
            'graph_data': graph_data,
        })


# Network Service Group graphite data
class NetworkServiceGroupGraphiteDataView(PermissionRequiredMixin, View):
    permission_required = 'sidekick.view_service'
    model = NetworkServiceGroup

    def get(self, request, pk):
        graphite_render_host = settings.PLUGINS_CONFIG['sidekick'].get('graphite_render_host', None)
        if graphite_render_host is None:
            return JsonResponse({})

        service_group = NetworkServiceGroup.objects.get(pk=self.kwargs['pk'])
        all_members = []
        all_services = []
        all_accounting_sources = []
        for network_service in service_group.network_services.all():
            member = network_service.member
            if member.name not in all_members:
                all_members.append(member.name)
                all_services.extend(get_services(member))
                all_accounting_sources.extend(get_accounting_sources(member))

        period = get_period(request)
        service_data = get_graphite_service_data(graphite_render_host, all_services, period)
        accounting_data = get_graphite_accounting_data(graphite_render_host, all_accounting_sources, period)
        remaining_data = get_graphite_remaining_data(graphite_render_host, all_services, period)

        graph_data = {
            'service_data': service_data['data'],
            'remaining_data': [service_data['data'][0], [0], [0]],
            'accounting_data': [service_data['data'][0], [0], [0]],
        }

        queries = {
            'service_data': service_data['query'],
            'remaining_data': remaining_data['query'],
            'accounting_data': accounting_data['query'],
        }

        if accounting_data is not None and 'data' in accounting_data:
            graph_data['accounting_data'] = accounting_data['data']

        if remaining_data is not None and 'data' in remaining_data:
            graph_data['remaining_data'] = remaining_data['data']

        return JsonResponse({
            'graph_data': graph_data,
            'queries': queries,
        })
