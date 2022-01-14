from django.conf import settings
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.http import JsonResponse
from django.views import View
from django_tables2.views import SingleTableView

from sidekick.tables import (
    MemberBandwidthTable,
)

from sidekick.models import (
    AccountingProfile,
    NetworkService,
)

from sidekick import utils

from tenancy.models import Tenant


def get_services(member):
    services = []
    accounting_sources = []
    for s in NetworkService.objects.filter(member__id=member.id):
        services.append(s.id)
    for a in AccountingProfile.objects.filter(member__id=member.id):
        for acct_source in a.accounting_sources.all():
            accounting_sources.append(acct_source.id)

    return (services, accounting_sources)


def get_period(request):
    period = request.GET.get('period', '-7d')
    if period not in ['-1d', '-7d', '-30d', '-1y', '-5y']:
        return None
    return period


class MemberBandwidthIndexView(PermissionRequiredMixin, SingleTableView):
    model = NetworkService
    permission_required = 'sidekick.view_memberbandwidth'
    table_class = MemberBandwidthTable
    table_pagination = False
    queryset = Tenant.objects.filter(group__name='Members')
    template_name = 'sidekick/memberbandwidth/memberbandwidth_index.html'


class MemberBandwidthDetailView(PermissionRequiredMixin, SingleTableView):
    permission_required = 'sidekick.view_memberbandwidth'
    model = NetworkService
    template_name = 'sidekick/memberbandwidth/memberbandwidth.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        member = Tenant.objects.get(id=self.kwargs['pk'])
        context['member'] = member

        (services, accounting_sources) = get_services(member)
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
        (services, accounting_sources) = get_services(member)
        period = get_period(request)
        service_data = utils.get_graphite_service_data(graphite_render_host, services, period)
        accounting_data = utils.get_graphite_accounting_data(graphite_render_host, accounting_sources, period)
        remaining_data = utils.get_graphite_remaining_data(graphite_render_host, services, period)

        graph_data = {
            'service_data': service_data['data'],
            'remaining_data': remaining_data['data'],
            'accounting_data': [service_data['data'][0], [0], [0]],
        }

        if accounting_data is not None and 'data' in accounting_data:
            graph_data['accounting_data'] = accounting_data['data']

        return JsonResponse({
            'graph_data': graph_data,
        })
