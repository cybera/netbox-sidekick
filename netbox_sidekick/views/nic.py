from django.conf import settings
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.views.generic import DetailView

from django_filters.views import FilterView
from django_tables2.views import SingleTableView

from dcim.models import Interface

from netbox_sidekick.filters import (
    NICFilterSet,
)

from netbox_sidekick.tables import (
    NICTable,
)

from netbox_sidekick.models import (
    NIC,
)

from netbox_sidekick.management.commands.sidekick_utils import (
    get_graphite_nic_graph
)


# NIC Index
# Displays devices that have NICs being managed by Sidekick
class NICIndexView(PermissionRequiredMixin, FilterView, SingleTableView):
    permission_required = 'netbox_sidekick.view_nic'
    model = NIC
    queryset = NIC.objects.order_by('interface__id').distinct('interface__id')
    table_class = NICTable
    filterset_class = NICFilterSet
    template_name = 'netbox_sidekick/nic/nic_device_index.html'


# NIC Details
class NICDetailView(PermissionRequiredMixin, DetailView):
    permission_required = 'netbox_sidekick.view_nic'
    model = Interface
    template_name = 'netbox_sidekick/nic/nic.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        nics = NIC.objects.filter(interface__id=self.kwargs['pk'])
        if len(nics) > 0:
            context['nic'] = nics[0]

            graphite_render_host = settings.PLUGINS_CONFIG['netbox_sidekick'].get('graphite_render_host', None)
            graph_data = get_graphite_nic_graph(nics[0], graphite_render_host)
            context['graph_data'] = graph_data

        return context
