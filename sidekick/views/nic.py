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
    get_graphite_nic_graph
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
        graphite_render_host = settings.PLUGINS_CONFIG['sidekick'].get('graphite_render_host', None)
        if graphite_render_host is None:
            return JsonResponse({})

        nics = NIC.objects.filter(interface__id=pk)
        if len(nics) > 0:
            graph_data = get_graphite_nic_graph(nics[0], graphite_render_host)
            return JsonResponse({
                'graph_data': graph_data,
            })
