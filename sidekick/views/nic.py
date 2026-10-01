from django.conf import settings
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.http import JsonResponse
from django.views import View

from netbox.views import generic
from utilities.views import register_model_view

from sidekick import filtersets, forms, tables
from sidekick.models import NIC
from sidekick.utils import (
    _service_has_clickhouse_backend,
    get_clickhouse_nic_graph,
    get_graphite_nic_graph,
)


#
# NICs
#
# NIC detail is rendered on the associated dcim.Interface via a template
# extension, so no dedicated detail view is registered.
#

@register_model_view(NIC, 'list', path='', detail=False)
class NICListView(generic.ObjectListView):
    queryset = NIC.objects.order_by('interface__id').distinct('interface__id')
    table = tables.NICTable
    filterset = filtersets.NICFilterSet
    filterset_form = filtersets.NICFilterSetForm


@register_model_view(NIC, 'add', detail=False)
@register_model_view(NIC, 'edit')
class NICEditView(generic.ObjectEditView):
    queryset = NIC.objects.order_by('interface__id').distinct('interface__id')
    form = forms.NICForm


@register_model_view(NIC, 'delete')
class NICDeleteView(generic.ObjectDeleteView):
    queryset = NIC.objects.order_by('interface__id').distinct('interface__id')


#
# NIC graphite data
#

class NICGraphiteDataView(PermissionRequiredMixin, View):
    permission_required = 'sidekick.view_nic'

    def get(self, request, pk):
        config = settings.PLUGINS_CONFIG.get('sidekick', {})
        use_clickhouse, ch_client = _service_has_clickhouse_backend(settings)

        if use_clickhouse and ch_client:
            nics = NIC.objects.filter(interface__id=pk)
            if len(nics) > 0:
                period = request.GET.get('period', '-1y')
                graph_data = get_clickhouse_nic_graph(nics[0], ch_client, period)
                if graph_data is None:
                    return JsonResponse({})
                return JsonResponse({
                    'graph_data': graph_data,
                })
            return JsonResponse({})

        # Fall back to Graphite
        graphite_render_host = config.get('graphite_render_host', None)
        if graphite_render_host is None:
            return JsonResponse({})

        nics = NIC.objects.filter(interface__id=pk)
        if len(nics) > 0:
            graph_data = get_graphite_nic_graph(nics[0], graphite_render_host)
            return JsonResponse({
                'graph_data': graph_data,
            })
