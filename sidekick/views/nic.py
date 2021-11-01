from django.conf import settings
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.http import JsonResponse
from django.views import View
from django.views.generic import DetailView

from django_filters.views import FilterView
from django_tables2.views import SingleTableView

from dcim.models import Interface

from sidekick.filters import (
    NICFilterSet,
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
class NICIndexView(PermissionRequiredMixin, FilterView, SingleTableView):
    permission_required = 'sidekick.view_nic'
    model = NIC
    queryset = NIC.objects.order_by('interface__id').distinct('interface__id')
    table_class = NICTable
    filterset_class = NICFilterSet
    template_name = 'sidekick/nic/nic_device_index.html'


# NIC Details
class NICDetailView(PermissionRequiredMixin, DetailView):
    permission_required = 'sidekick.view_nic'
    model = Interface
    template_name = 'sidekick/nic/nic.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        nics = NIC.objects.filter(interface__id=self.kwargs['pk'])
        if len(nics) > 0:
            context['nic'] = nics[0]

        return context


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
