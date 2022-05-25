from django.conf import settings
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.http import JsonResponse
from django.views import View
from django_tables2.views import SingleTableView

from sidekick.tables import (
    MemberBandwidthTable,
)

from sidekick.models import (
    NetworkService,
)

from sidekick import utils

from tenancy.models import Tenant


class MemberBandwidthIndexView(PermissionRequiredMixin, SingleTableView):
    model = NetworkService
    permission_required = 'sidekick.view_memberbandwidth'
    table_class = MemberBandwidthTable
    table_pagination = False
    queryset = Tenant.objects.filter(group__name='Members')
    template_name = 'sidekick/memberbandwidth_list.html'


class MemberBandwidthDetailView(PermissionRequiredMixin, SingleTableView):
    permission_required = 'sidekick.view_memberbandwidth'
    model = NetworkService
    template_name = 'sidekick/memberbandwidth.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        member = Tenant.objects.get(id=self.kwargs['pk'])
        context['member'] = member

        accounting_sources = utils.get_accounting_sources(member)
        if len(accounting_sources) > 0:
            context['accounting'] = True

        return context


class MemberBandwidthDataView(PermissionRequiredMixin, View):
    permission_required = 'sidekick.view_memberbandwidth'
    model = NetworkService

    def get(self, request, pk):
        graphite_render_host = settings.PLUGINS_CONFIG['sidekick'].get('graphite_render_host', None)
        if graphite_render_host is None:
            return JsonResponse({})

        member = Tenant.objects.get(pk=pk)
        services = utils.get_services(member)
        period = utils.get_period(request)
        (services_in, services_out) = utils.format_graphite_service_query(services)
        service_data = utils.get_graphite_data(graphite_render_host, [services_in], [services_out], period)

        accounting_data = None
        accounting_sources = utils.get_accounting_sources(member)
        if len(accounting_sources) > 0:
            (accounting_in, accounting_out) = utils.format_graphite_accounting_query(accounting_sources)
            accounting_data = utils.get_graphite_data(graphite_render_host, [accounting_in], [accounting_out], period)

        (remaining_in, remaining_out) = utils.format_graphite_remaining_query(services, accounting_sources)
        remaining_data = utils.get_graphite_data(graphite_render_host, [remaining_in], [remaining_out], period)

        graph_data = {
            'service_data': service_data['data'],
            'remaining_data': [service_data['data'][0], [0], [0]],
            'accounting_data': [service_data['data'][0], [0], [0]],
        }

        queries = {
            'service_data': service_data['query'],
        }

        if accounting_data is not None and 'data' in accounting_data:
            graph_data['accounting_data'] = accounting_data['data']
            queries['accounting_data'] = accounting_data['query']

        if remaining_data is not None and 'data' in remaining_data:
            graph_data['remaining_data'] = remaining_data['data']
            queries['remaiing_data'] = remaining_data['query']

        return JsonResponse({
            'graph_data': graph_data,
            'queries': queries,
        })
