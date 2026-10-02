from django.conf import settings
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.http import JsonResponse
from django.views import View

from netbox.views import generic
from utilities.views import register_model_view

from sidekick import filtersets, forms, tables, utils
from sidekick.models import (
    LogicalSystem,
    RoutingType,
    NetworkServiceType,
    NetworkService,
    NetworkServiceDevice,
    NetworkServiceL2,
    NetworkServiceL3,
    NetworkServiceGroup,
)
from sidekick.ui import panels
from sidekick.utils import (
    _service_has_clickhouse_backend,
    get_clickhouse_service_graph,
    get_clickhouse_service_group_bandwidth,
)

from .base import SidekickObjectView


#
# Logical systems
#

@register_model_view(LogicalSystem, 'list', path='', detail=False)
class LogicalSystemListView(generic.ObjectListView):
    queryset = LogicalSystem.objects.all()
    table = tables.LogicalSystemTable
    filterset = filtersets.LogicalSystemFilterSet
    filterset_form = filtersets.LogicalSystemFilterSetForm


@register_model_view(LogicalSystem)
class LogicalSystemView(SidekickObjectView):
    queryset = LogicalSystem.objects.all()
    layout = panels.LOGICAL_SYSTEM_LAYOUT


@register_model_view(LogicalSystem, 'add', detail=False)
@register_model_view(LogicalSystem, 'edit')
class LogicalSystemEditView(generic.ObjectEditView):
    queryset = LogicalSystem.objects.all()
    form = forms.LogicalSystemForm


@register_model_view(LogicalSystem, 'delete')
class LogicalSystemDeleteView(generic.ObjectDeleteView):
    queryset = LogicalSystem.objects.all()


#
# Routing types
#

@register_model_view(RoutingType, 'list', path='', detail=False)
class RoutingTypeListView(generic.ObjectListView):
    queryset = RoutingType.objects.all()
    table = tables.RoutingTypeTable
    filterset = filtersets.RoutingTypeFilterSet
    filterset_form = filtersets.RoutingTypeFilterSetForm


@register_model_view(RoutingType)
class RoutingTypeView(SidekickObjectView):
    queryset = RoutingType.objects.all()
    layout = panels.ROUTING_TYPE_LAYOUT


@register_model_view(RoutingType, 'add', detail=False)
@register_model_view(RoutingType, 'edit')
class RoutingTypeEditView(generic.ObjectEditView):
    queryset = RoutingType.objects.all()
    form = forms.RoutingTypeForm


@register_model_view(RoutingType, 'delete')
class RoutingTypeDeleteView(generic.ObjectDeleteView):
    queryset = RoutingType.objects.all()


#
# Network service types
#

@register_model_view(NetworkServiceType, 'list', path='', detail=False)
class NetworkServiceTypeListView(generic.ObjectListView):
    queryset = NetworkServiceType.objects.all()
    table = tables.NetworkServiceTypeTable
    filterset = filtersets.NetworkServiceTypeFilterSet
    filterset_form = filtersets.NetworkServiceTypeFilterSetForm


@register_model_view(NetworkServiceType)
class NetworkServiceTypeView(SidekickObjectView):
    queryset = NetworkServiceType.objects.all()
    layout = panels.NETWORK_SERVICE_TYPE_LAYOUT


@register_model_view(NetworkServiceType, 'add', detail=False)
@register_model_view(NetworkServiceType, 'edit')
class NetworkServiceTypeEditView(generic.ObjectEditView):
    queryset = NetworkServiceType.objects.all()
    form = forms.NetworkServiceTypeForm


@register_model_view(NetworkServiceType, 'delete')
class NetworkServiceTypeDeleteView(generic.ObjectDeleteView):
    queryset = NetworkServiceType.objects.all()


#
# Network services
#

@register_model_view(NetworkService, 'list', path='', detail=False)
class NetworkServiceListView(generic.ObjectListView):
    queryset = NetworkService.objects.all()
    table = tables.NetworkServiceTable
    filterset = filtersets.NetworkServiceFilterSet
    filterset_form = filtersets.NetworkServiceFilterSetForm


@register_model_view(NetworkService)
class NetworkServiceView(SidekickObjectView):
    queryset = NetworkService.objects.prefetch_related(
        'network_service_devices__device',
        'network_service_devices__network_service_l2',
        'network_service_devices__network_service_l3__ip_prefixes',
    )
    layout = panels.NETWORK_SERVICE_LAYOUT


@register_model_view(NetworkService, 'add', detail=False)
@register_model_view(NetworkService, 'edit')
class NetworkServiceEditView(generic.ObjectEditView):
    queryset = NetworkService.objects.all()
    form = forms.NetworkServiceForm


@register_model_view(NetworkService, 'delete')
class NetworkServiceDeleteView(generic.ObjectDeleteView):
    queryset = NetworkService.objects.all()


#
# Network service devices
#

@register_model_view(NetworkServiceDevice, 'list', path='', detail=False)
class NetworkServiceDeviceListView(generic.ObjectListView):
    queryset = NetworkServiceDevice.objects.all()
    table = tables.NetworkServiceDeviceTable
    filterset = filtersets.NetworkServiceDeviceFilterSet
    filterset_form = filtersets.NetworkServiceDeviceFilterSetForm


@register_model_view(NetworkServiceDevice)
class NetworkServiceDeviceView(SidekickObjectView):
    queryset = NetworkServiceDevice.objects.all()
    layout = panels.NETWORK_SERVICE_DEVICE_LAYOUT


@register_model_view(NetworkServiceDevice, 'add', detail=False)
@register_model_view(NetworkServiceDevice, 'edit')
class NetworkServiceDeviceEditView(generic.ObjectEditView):
    queryset = NetworkServiceDevice.objects.all()
    form = forms.NetworkServiceDeviceForm
    template_name = 'sidekick/networkservicedevice_edit.html'


@register_model_view(NetworkServiceDevice, 'delete')
class NetworkServiceDeviceDeleteView(generic.ObjectDeleteView):
    queryset = NetworkServiceDevice.objects.all()


#
# Network service L2
#

@register_model_view(NetworkServiceL2, 'list', path='', detail=False)
class NetworkServiceL2ListView(generic.ObjectListView):
    queryset = NetworkServiceL2.objects.all()
    table = tables.NetworkServiceL2Table
    filterset = filtersets.NetworkServiceL2FilterSet
    filterset_form = filtersets.NetworkServiceL2FilterSetForm


@register_model_view(NetworkServiceL2)
class NetworkServiceL2View(SidekickObjectView):
    queryset = NetworkServiceL2.objects.all()
    layout = panels.NETWORK_SERVICE_L2_LAYOUT


@register_model_view(NetworkServiceL2, 'add', detail=False)
@register_model_view(NetworkServiceL2, 'edit')
class NetworkServiceL2EditView(generic.ObjectEditView):
    queryset = NetworkServiceL2.objects.all()
    form = forms.NetworkServiceL2Form


@register_model_view(NetworkServiceL2, 'delete')
class NetworkServiceL2DeleteView(generic.ObjectDeleteView):
    queryset = NetworkServiceL2.objects.all()


#
# Network service L3
#

@register_model_view(NetworkServiceL3, 'list', path='', detail=False)
class NetworkServiceL3ListView(generic.ObjectListView):
    queryset = NetworkServiceL3.objects.all()
    table = tables.NetworkServiceL3Table
    filterset = filtersets.NetworkServiceL3FilterSet
    filterset_form = filtersets.NetworkServiceL3FilterSetForm


@register_model_view(NetworkServiceL3)
class NetworkServiceL3View(SidekickObjectView):
    queryset = NetworkServiceL3.objects.all()
    layout = panels.NETWORK_SERVICE_L3_LAYOUT


@register_model_view(NetworkServiceL3, 'add', detail=False)
@register_model_view(NetworkServiceL3, 'edit')
class NetworkServiceL3EditView(generic.ObjectEditView):
    queryset = NetworkServiceL3.objects.all()
    form = forms.NetworkServiceL3Form


@register_model_view(NetworkServiceL3, 'delete')
class NetworkServiceL3DeleteView(generic.ObjectDeleteView):
    queryset = NetworkServiceL3.objects.all()


#
# Network service groups
#

@register_model_view(NetworkServiceGroup, 'list', path='', detail=False)
class NetworkServiceGroupListView(generic.ObjectListView):
    queryset = NetworkServiceGroup.objects.all()
    table = tables.NetworkServiceGroupTable
    filterset = filtersets.NetworkServiceGroupFilterSet
    filterset_form = filtersets.NetworkServiceGroupFilterSetForm


@register_model_view(NetworkServiceGroup)
class NetworkServiceGroupView(SidekickObjectView):
    queryset = NetworkServiceGroup.objects.all()
    layout = panels.NETWORK_SERVICE_GROUP_LAYOUT


@register_model_view(NetworkServiceGroup, 'add', detail=False)
@register_model_view(NetworkServiceGroup, 'edit')
class NetworkServiceGroupEditView(generic.ObjectEditView):
    queryset = NetworkServiceGroup.objects.all()
    form = forms.NetworkServiceGroupForm


@register_model_view(NetworkServiceGroup, 'delete')
class NetworkServiceGroupDeleteView(generic.ObjectDeleteView):
    queryset = NetworkServiceGroup.objects.all()


#
# Bulk operations
#

@register_model_view(LogicalSystem, 'bulk_import', path='import', detail=False)
class LogicalSystemBulkImportView(generic.BulkImportView):
    queryset = LogicalSystem.objects.all()
    model_form = forms.LogicalSystemImportForm


@register_model_view(LogicalSystem, 'bulk_edit', path='edit', detail=False)
class LogicalSystemBulkEditView(generic.BulkEditView):
    queryset = LogicalSystem.objects.all()
    filterset = filtersets.LogicalSystemFilterSet
    table = tables.LogicalSystemTable
    form = forms.LogicalSystemBulkEditForm


@register_model_view(LogicalSystem, 'bulk_rename', path='rename', detail=False)
class LogicalSystemBulkRenameView(generic.BulkRenameView):
    queryset = LogicalSystem.objects.all()
    filterset = filtersets.LogicalSystemFilterSet


@register_model_view(LogicalSystem, 'bulk_delete', path='delete', detail=False)
class LogicalSystemBulkDeleteView(generic.BulkDeleteView):
    queryset = LogicalSystem.objects.all()
    filterset = filtersets.LogicalSystemFilterSet
    table = tables.LogicalSystemTable


@register_model_view(RoutingType, 'bulk_import', path='import', detail=False)
class RoutingTypeBulkImportView(generic.BulkImportView):
    queryset = RoutingType.objects.all()
    model_form = forms.RoutingTypeImportForm


@register_model_view(RoutingType, 'bulk_edit', path='edit', detail=False)
class RoutingTypeBulkEditView(generic.BulkEditView):
    queryset = RoutingType.objects.all()
    filterset = filtersets.RoutingTypeFilterSet
    table = tables.RoutingTypeTable
    form = forms.RoutingTypeBulkEditForm


@register_model_view(RoutingType, 'bulk_rename', path='rename', detail=False)
class RoutingTypeBulkRenameView(generic.BulkRenameView):
    queryset = RoutingType.objects.all()
    filterset = filtersets.RoutingTypeFilterSet


@register_model_view(RoutingType, 'bulk_delete', path='delete', detail=False)
class RoutingTypeBulkDeleteView(generic.BulkDeleteView):
    queryset = RoutingType.objects.all()
    filterset = filtersets.RoutingTypeFilterSet
    table = tables.RoutingTypeTable


@register_model_view(NetworkServiceType, 'bulk_import', path='import', detail=False)
class NetworkServiceTypeBulkImportView(generic.BulkImportView):
    queryset = NetworkServiceType.objects.all()
    model_form = forms.NetworkServiceTypeImportForm


@register_model_view(NetworkServiceType, 'bulk_edit', path='edit', detail=False)
class NetworkServiceTypeBulkEditView(generic.BulkEditView):
    queryset = NetworkServiceType.objects.all()
    filterset = filtersets.NetworkServiceTypeFilterSet
    table = tables.NetworkServiceTypeTable
    form = forms.NetworkServiceTypeBulkEditForm


@register_model_view(NetworkServiceType, 'bulk_rename', path='rename', detail=False)
class NetworkServiceTypeBulkRenameView(generic.BulkRenameView):
    queryset = NetworkServiceType.objects.all()
    filterset = filtersets.NetworkServiceTypeFilterSet


@register_model_view(NetworkServiceType, 'bulk_delete', path='delete', detail=False)
class NetworkServiceTypeBulkDeleteView(generic.BulkDeleteView):
    queryset = NetworkServiceType.objects.all()
    filterset = filtersets.NetworkServiceTypeFilterSet
    table = tables.NetworkServiceTypeTable


@register_model_view(NetworkService, 'bulk_import', path='import', detail=False)
class NetworkServiceBulkImportView(generic.BulkImportView):
    queryset = NetworkService.objects.all()
    model_form = forms.NetworkServiceImportForm


@register_model_view(NetworkService, 'bulk_edit', path='edit', detail=False)
class NetworkServiceBulkEditView(generic.BulkEditView):
    queryset = NetworkService.objects.all()
    filterset = filtersets.NetworkServiceFilterSet
    table = tables.NetworkServiceTable
    form = forms.NetworkServiceBulkEditForm


@register_model_view(NetworkService, 'bulk_rename', path='rename', detail=False)
class NetworkServiceBulkRenameView(generic.BulkRenameView):
    queryset = NetworkService.objects.all()
    filterset = filtersets.NetworkServiceFilterSet


@register_model_view(NetworkService, 'bulk_delete', path='delete', detail=False)
class NetworkServiceBulkDeleteView(generic.BulkDeleteView):
    queryset = NetworkService.objects.all()
    filterset = filtersets.NetworkServiceFilterSet
    table = tables.NetworkServiceTable


@register_model_view(NetworkServiceDevice, 'bulk_import', path='import', detail=False)
class NetworkServiceDeviceBulkImportView(generic.BulkImportView):
    queryset = NetworkServiceDevice.objects.all()
    model_form = forms.NetworkServiceDeviceImportForm


@register_model_view(NetworkServiceDevice, 'bulk_edit', path='edit', detail=False)
class NetworkServiceDeviceBulkEditView(generic.BulkEditView):
    queryset = NetworkServiceDevice.objects.all()
    filterset = filtersets.NetworkServiceDeviceFilterSet
    table = tables.NetworkServiceDeviceTable
    form = forms.NetworkServiceDeviceBulkEditForm


@register_model_view(NetworkServiceDevice, 'bulk_delete', path='delete', detail=False)
class NetworkServiceDeviceBulkDeleteView(generic.BulkDeleteView):
    queryset = NetworkServiceDevice.objects.all()
    filterset = filtersets.NetworkServiceDeviceFilterSet
    table = tables.NetworkServiceDeviceTable


@register_model_view(NetworkServiceL2, 'bulk_import', path='import', detail=False)
class NetworkServiceL2BulkImportView(generic.BulkImportView):
    queryset = NetworkServiceL2.objects.all()
    model_form = forms.NetworkServiceL2ImportForm


@register_model_view(NetworkServiceL2, 'bulk_edit', path='edit', detail=False)
class NetworkServiceL2BulkEditView(generic.BulkEditView):
    queryset = NetworkServiceL2.objects.all()
    filterset = filtersets.NetworkServiceL2FilterSet
    table = tables.NetworkServiceL2Table
    form = forms.NetworkServiceL2BulkEditForm


@register_model_view(NetworkServiceL2, 'bulk_delete', path='delete', detail=False)
class NetworkServiceL2BulkDeleteView(generic.BulkDeleteView):
    queryset = NetworkServiceL2.objects.all()
    filterset = filtersets.NetworkServiceL2FilterSet
    table = tables.NetworkServiceL2Table


@register_model_view(NetworkServiceL3, 'bulk_import', path='import', detail=False)
class NetworkServiceL3BulkImportView(generic.BulkImportView):
    queryset = NetworkServiceL3.objects.all()
    model_form = forms.NetworkServiceL3ImportForm


@register_model_view(NetworkServiceL3, 'bulk_edit', path='edit', detail=False)
class NetworkServiceL3BulkEditView(generic.BulkEditView):
    queryset = NetworkServiceL3.objects.all()
    filterset = filtersets.NetworkServiceL3FilterSet
    table = tables.NetworkServiceL3Table
    form = forms.NetworkServiceL3BulkEditForm


@register_model_view(NetworkServiceL3, 'bulk_delete', path='delete', detail=False)
class NetworkServiceL3BulkDeleteView(generic.BulkDeleteView):
    queryset = NetworkServiceL3.objects.all()
    filterset = filtersets.NetworkServiceL3FilterSet
    table = tables.NetworkServiceL3Table


@register_model_view(NetworkServiceGroup, 'bulk_import', path='import', detail=False)
class NetworkServiceGroupBulkImportView(generic.BulkImportView):
    queryset = NetworkServiceGroup.objects.all()
    model_form = forms.NetworkServiceGroupImportForm


@register_model_view(NetworkServiceGroup, 'bulk_edit', path='edit', detail=False)
class NetworkServiceGroupBulkEditView(generic.BulkEditView):
    queryset = NetworkServiceGroup.objects.all()
    filterset = filtersets.NetworkServiceGroupFilterSet
    table = tables.NetworkServiceGroupTable
    form = forms.NetworkServiceGroupBulkEditForm


@register_model_view(NetworkServiceGroup, 'bulk_rename', path='rename', detail=False)
class NetworkServiceGroupBulkRenameView(generic.BulkRenameView):
    queryset = NetworkServiceGroup.objects.all()
    filterset = filtersets.NetworkServiceGroupFilterSet


@register_model_view(NetworkServiceGroup, 'bulk_delete', path='delete', detail=False)
class NetworkServiceGroupBulkDeleteView(generic.BulkDeleteView):
    queryset = NetworkServiceGroup.objects.all()
    filterset = filtersets.NetworkServiceGroupFilterSet
    table = tables.NetworkServiceGroupTable


#
# Peering connections (read-only list of L3 services assigned to a member)
#

class PeeringConnectionListView(generic.ObjectListView):
    queryset = NetworkServiceL3.objects.filter(member__isnull=False)
    table = tables.PeeringConnectionTable
    filterset = filtersets.PeeringConnectionFilterSet
    filterset_form = filtersets.PeeringConnectionFilterSetForm


#
# Graph data endpoints
#

class NetworkServiceGraphiteDataView(PermissionRequiredMixin, View):
    permission_required = 'sidekick.view_networkservice'

    def get(self, request, pk):
        config = settings.PLUGINS_CONFIG.get('sidekick', {})
        use_clickhouse, ch_client = _service_has_clickhouse_backend(settings)

        if use_clickhouse and ch_client:
            network_service = NetworkService.objects.get(pk=self.kwargs['pk'])
            period = request.GET.get('period', '-1y')
            graph_data = get_clickhouse_service_graph(network_service, ch_client, period)
            if graph_data is None:
                return JsonResponse({})
            return JsonResponse({
                'graph_data': graph_data,
            })

        # Fall back to Graphite
        graphite_render_host = config.get('graphite_render_host', None)
        if graphite_render_host is None:
            return JsonResponse({})

        network_service = NetworkService.objects.get(pk=self.kwargs['pk'])
        graph_data = utils.get_graphite_service_graph(graphite_render_host, network_service)
        return JsonResponse({
            'graph_data': graph_data,
        })


class NetworkServiceGroupGraphiteDataView(PermissionRequiredMixin, View):
    permission_required = 'sidekick.view_networkservicegroup'

    def get(self, request, pk):
        config = settings.PLUGINS_CONFIG.get('sidekick', {})
        use_clickhouse, ch_client = _service_has_clickhouse_backend(settings)

        period = utils.get_period(request) or '-1y'

        if use_clickhouse and ch_client:
            service_group = NetworkServiceGroup.objects.get(pk=self.kwargs['pk'])
            results = get_clickhouse_service_group_bandwidth(ch_client, service_group, period)
            if results is None:
                return JsonResponse({})
            return JsonResponse({
                'graph_data': {
                    'service_data': results['service_data']['data'],
                    'accounting_data': results['accounting_data']['data'],
                    'remaining_data': results['remaining_data']['data'],
                },
                'queries': {
                    'service_data': results['service_data']['query'],
                    'accounting_data': results['accounting_data']['query'],
                    'remaining_data': results['remaining_data']['query'],
                },
            })

        # Fall back to Graphite
        graphite_render_host = config.get('graphite_render_host', None)
        if graphite_render_host is None:
            return JsonResponse({})

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
