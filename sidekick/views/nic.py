from netbox.views.generic import (
    ObjectView, ObjectListView,
    ObjectEditView, ObjectDeleteView,
)

from django.conf import settings
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.http import JsonResponse
from django.views import View

from dcim.models import Interface

from sidekick.filters import (
    NICFilterSet,
    NICFilterSetForm,
)

from sidekick.forms import (
    NICForm
)

from sidekick.tables import (
    NICTable,
)

from sidekick.models import (
    NIC,
)

from sidekick.utils import (
    get_graphite_nic_graph,
    get_clickhouse_nic_graph,
    _service_has_clickhouse_backend,
)


# NIC Index
# Displays devices that have NICs being managed by Sidekick
class NICIndexView(ObjectListView):
    queryset = NIC.objects.order_by('interface__id').distinct('interface__id')
    model = NIC
    table = NICTable
    filterset = NICFilterSet
    filterset_form = NICFilterSetForm


# NIC Details
class NICDetailView(ObjectView):
    queryset = NIC.objects.order_by('interface__id').distinct('interface__id')


# NIC Edit
class NICEditView(ObjectEditView):
    queryset = NIC.objects.order_by('interface__id').distinct('interface__id')
    form = NICForm


# NIC Delete
class NICDeleteView(ObjectDeleteView):
    queryset = NIC.objects.order_by('interface__id').distinct('interface__id')


# NIC graphite data
class NICGraphiteDataView(PermissionRequiredMixin, View):
    permission_required = 'sidekick.view_nic'
    model = Interface

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
