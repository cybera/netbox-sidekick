from netbox.views.generic import (
    ObjectView, ObjectListView,
    ObjectEditView, ObjectDeleteView,
)

from django.conf import settings
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.http import JsonResponse
from django.views import View

from django_tables2.views import SingleTableView

from sidekick.filters import (
    LogicalSystemFilterSet,
    LogicalSystemFilterSetForm,
    RoutingTypeFilterSet,
    RoutingTypeFilterSetForm,
    NetworkServiceTypeFilterSet,
    NetworkServiceTypeFilterSetForm,
    NetworkServiceFilterSet,
    NetworkServiceFilterSetForm,
    NetworkServiceL3FilterSet,
    NetworkServiceL3FilterSetForm,
    NetworkServiceGroupFilterSet,
    NetworkServiceGroupFilterSetForm,
    PeeringConnectionFilterSet,
    PeeringConnectionFilterSetForm,
)

from sidekick.forms import (
    RoutingTypeForm,
    LogicalSystemForm,
    NetworkServiceForm,
    NetworkServiceL3Form,
    NetworkServiceTypeForm,
    NetworkServiceGroupForm,
)

from sidekick.tables import (
    IPPrefixTable,
    LogicalSystemTable,
    NetworkServiceTypeTable,
    NetworkServiceTable,
    NetworkServiceL3Table,
    NetworkServiceGroupTable,
    PeeringConnectionTable,
    RoutingTypeTable,
)

from sidekick.models import (
    LogicalSystem,
    RoutingType,
    NetworkServiceType,
    NetworkService,
    NetworkServiceL3,
    NetworkServiceGroup,
)

from sidekick import utils


# IP Prefix Index
class IPPrefixIndexView(PermissionRequiredMixin, SingleTableView):
    permission_required = 'sidekick.view_ipprefix'
    model = NetworkService
    template_name = 'sidekick/ipprefix_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        prefixes = []
        for member_id, data in utils.get_all_ip_prefixes().items():
            for prefix in data['prefixes']:
                prefixes.append({
                    'prefix': prefix,
                    'member': data['member'],
                })
        context['ipprefix_table'] = IPPrefixTable(prefixes)

        return context


# Logical System Index
class LogicalSystemIndexView(ObjectListView):
    queryset = LogicalSystem.objects.all()
    model = LogicalSystem
    table = LogicalSystemTable
    filterset = LogicalSystemFilterSet
    filterset_form = LogicalSystemFilterSetForm


# Logical System Details
class LogicalSystemDetailView(ObjectView):
    queryset = LogicalSystem.objects.all()

    def get_extra_context(self, request, instance):
        table = NetworkServiceTable(
            NetworkService.objects.filter(
                network_service_devices__network_service_l3__logical_system=instance.id))

        return {'networkservice_table': table}


# Logical System Edit
class LogicalSystemEditView(ObjectEditView):
    queryset = LogicalSystem.objects.all()
    form = LogicalSystemForm


# Logical System Delete
class LogicalSystemDeleteView(ObjectDeleteView):
    queryset = LogicalSystem.objects.all()


# Routing Type Index
class RoutingTypeIndexView(ObjectListView):
    queryset = RoutingType.objects.all()
    model = RoutingType
    table = RoutingTypeTable
    filterset = RoutingTypeFilterSet
    filterset_form = RoutingTypeFilterSetForm


# Routing Type Details
class RoutingTypeDetailView(ObjectView):
    queryset = RoutingType.objects.all()

    def get_extra_context(self, request, instance):
        table = NetworkServiceTable(
            NetworkService.objects.filter(
                network_service_devices__network_service_l3__routing_type=instance.id))

        return {'networkservice_table': table}


# Routing Type Edit
class RoutingTypeEditView(ObjectEditView):
    queryset = RoutingType.objects.all()
    form = RoutingTypeForm


# Routing Type Delete
class RoutingTypeDeleteView(ObjectDeleteView):
    queryset = RoutingType.objects.all()


# Network Service Type Index
class NetworkServiceTypeIndexView(ObjectListView):
    queryset = NetworkServiceType.objects.all()
    model = NetworkServiceType
    table = NetworkServiceTypeTable
    filterset = NetworkServiceTypeFilterSet
    filterset_form = NetworkServiceTypeFilterSetForm


# Network Service Type Details
class NetworkServiceTypeDetailView(ObjectView):
    queryset = NetworkServiceType.objects.all()

    def get_extra_context(self, request, instance):
        table = NetworkServiceTable(
            NetworkService.objects.filter(
                network_service_type=instance.id))

        return {'networkservice_table': table}


# Network Service Type Edit
class NetworkServiceTypeEditView(ObjectEditView):
    queryset = NetworkServiceType.objects.all()
    form = NetworkServiceTypeForm


# Network Service Type Delete
class NetworkServiceTypeDeleteView(ObjectDeleteView):
    queryset = NetworkServiceType.objects.all()


# Network Service Index
class NetworkServiceIndexView(ObjectListView):
    queryset = NetworkService.objects.all()
    model = NetworkService
    table = NetworkServiceTable
    filterset = NetworkServiceFilterSet
    filterset_form = NetworkServiceFilterSetForm


# Network Service Details
class NetworkServiceDetailView(ObjectView):
    queryset = NetworkService.objects.all()


# Network Service Edit
class NetworkServiceEditView(ObjectEditView):
    queryset = NetworkService.objects.all()
    form = NetworkServiceForm


# Network Service Delete
class NetworkServiceDeleteView(ObjectDeleteView):
    queryset = NetworkService.objects.all()


# Network Service L3 Index
class NetworkServiceL3IndexView(ObjectListView):
    queryset = NetworkServiceL3.objects.all()
    model = NetworkServiceL3
    table = NetworkServiceL3Table
    filterset = NetworkServiceL3FilterSet
    filterset_form = NetworkServiceL3FilterSetForm


# Network Service L3 Details
class NetworkServiceL3DetailView(ObjectView):
    queryset = NetworkServiceL3.objects.all()


# Network Service L3 Edit
class NetworkServiceL3EditView(ObjectEditView):
    queryset = NetworkServiceL3.objects.all()
    form = NetworkServiceL3Form


# Network Service L3 Delete
class NetworkServiceL3DeleteView(ObjectDeleteView):
    queryset = NetworkServiceL3.objects.all()


# Network Service Group Index
class NetworkServiceGroupIndexView(ObjectListView):
    queryset = NetworkServiceGroup.objects.all()
    model = NetworkServiceGroup
    table = NetworkServiceGroupTable
    filterset = NetworkServiceGroupFilterSet
    filterset_form = NetworkServiceGroupFilterSetForm


# Network Service Group Details
class NetworkServiceGroupDetailView(ObjectView):
    queryset = NetworkServiceGroup.objects.all()

    def get_extra_context(self, request, instance):
        table = NetworkServiceTable(
            NetworkService.objects.filter(
                pk__in=instance.network_services.all()))

        return {'networkservice_table': table}


# Network Service Group Edit
class NetworkServiceGroupEditView(ObjectEditView):
    queryset = NetworkServiceGroup.objects.all()
    form = NetworkServiceGroupForm


# Network Service Group Delete
class NetworkServiceGroupDeleteView(ObjectDeleteView):
    queryset = NetworkServiceGroup.objects.all()


# Network Service graphite data
class NetworkServiceGraphiteDataView(PermissionRequiredMixin, View):
    permission_required = 'sidekick.view_service'
    model = NetworkService

    def get(self, request, pk):
        graphite_render_host = settings.PLUGINS_CONFIG['sidekick'].get('graphite_render_host', None)
        if graphite_render_host is None:
            return JsonResponse({})

        network_service = NetworkService.objects.get(pk=self.kwargs['pk'])
        graph_data = utils.get_graphite_service_graph(graphite_render_host, network_service)
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

        period = utils.get_period(request)

        services_by_member = {}
        accounting_by_member = {}
        service_group = NetworkServiceGroup.objects.get(pk=self.kwargs['pk'])
        for network_service in service_group.network_services.all():
            member = network_service.member
            if member.name not in services_by_member.keys():
                services_by_member[member.name] = []
            if member.name not in accounting_by_member.keys():
                accounting_by_member[member.name] = []

            services_by_member[member.name].append(network_service)
            accounting_by_member[member.name] = utils.get_accounting_sources(member)

        services_in = []
        services_out = []
        accounting_in = []
        accounting_out = []
        remaining_in = []
        remaining_out = []
        for member_name in services_by_member.keys():
            services = services_by_member[member_name]
            accounting = accounting_by_member[member_name]

            (_in, _out) = utils.format_graphite_service_query(services)
            services_in.append(_in)
            services_out.append(_out)

            (_in, _out) = utils.format_graphite_accounting_query(accounting)
            accounting_in.append(_in)
            accounting_out.append(_out)

            (_in, _out) = utils.format_graphite_remaining_query(services, accounting)
            remaining_in.append(_in)
            remaining_out.append(_out)

        service_data = utils.get_graphite_data(graphite_render_host, services_in, services_out, period)
        accounting_data = utils.get_graphite_data(graphite_render_host, accounting_in, accounting_out, period)
        remaining_data = utils.get_graphite_data(graphite_render_host, remaining_in, remaining_out, period)

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


# Peering Service Index
class PeeringConnectionIndexView(ObjectListView):
    queryset = NetworkServiceL3.objects.filter(
        member__isnull=False)
    model = NetworkServiceL3
    table = PeeringConnectionTable
    filterset = PeeringConnectionFilterSet
    filterset_form = PeeringConnectionFilterSetForm


# Peering Service Details
class PeeringConnectionDetailView(ObjectView):
    template_name = 'sidekick/peeringconnection.html'
    queryset = NetworkServiceL3.objects.filter(
        member__isnull=False)


# Peering Service Edit
class PeeringConnectionEditView(ObjectEditView):
    queryset = NetworkServiceL3.objects.filter(
        member__isnull=False)
    form = NetworkServiceL3Form


# Peering Delete Edit
class PeeringConnectionDeleteView(ObjectDeleteView):
    queryset = NetworkServiceL3.objects.filter(
        member__isnull=False)
