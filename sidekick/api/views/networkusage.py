from django.conf import settings
from django.http import Http404

from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.renderers import JSONRenderer
from rest_framework.views import APIView

from netbox.api.authentication import TokenAuthentication

from sidekick import utils
from sidekick.utils import (
    get_clickhouse_member_bandwidth,
    _service_has_clickhouse_backend,
)
from sidekick.models import (
    NetworkServiceGroup,
)

from tenancy.models import Tenant


class NetworkUsageListGroupsView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    renderer_class = JSONRenderer

    def get(self, request):
        result = []
        for g in NetworkServiceGroup.objects.all():
            result.append({
                "id": g.id,
                "name": g.name,
            })

        return Response(result)


class NetworkUsageListMembersView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    renderer_class = JSONRenderer

    def get(self, request):
        result = []
        for t in Tenant.objects.filter(group__name='Members'):
            result.append({
                "id": t.id,
                "name": t.name,
            })

        return Response(result)


class NetworkUsageGroupView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    renderer_class = JSONRenderer

    def get(self, request, group_id=None):
        group_id = self.kwargs.get('group_id', None)
        if group_id is None:
            raise Http404

        try:
            service_group = NetworkServiceGroup.objects.get(id=group_id)
        except NetworkServiceGroup.DoesNotExist:
            raise Http404

        period = utils.get_period(request) or '-1y'

        use_clickhouse, ch_client = _service_has_clickhouse_backend(settings)

        if use_clickhouse and ch_client:
            results = get_clickhouse_service_group_bandwidth(ch_client, service_group, period)
            if results is None:
                return Response({})
            return Response({
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
        graphite_render_host = settings.PLUGINS_CONFIG.get('sidekick', {}).get('graphite_render_host', None)
        if graphite_render_host is None:
            return Response({})

        services_by_member = {}
        accounting_by_member = {}
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

        return Response({
            'graph_data': graph_data,
            'queries': queries,
        })


class NetworkUsageMemberView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    renderer_class = JSONRenderer

    def get(self, request, member_id=None):
        member_id = self.kwargs.get('member_id', None)
        if member_id is None:
            raise Http404

        try:
            member = Tenant.objects.get(id=member_id)
        except Tenant.DoesNotExist:
            raise Http404

        services = utils.get_services_for_graphite(member)
        accounting_sources = utils.get_accounting_sources(member)
        period = utils.get_period(request) or '-1y'

        use_clickhouse, ch_client = _service_has_clickhouse_backend(settings)

        if use_clickhouse and ch_client:
            results = get_clickhouse_member_bandwidth(ch_client, member, services, accounting_sources, period)
            if results is None:
                return Response({})
            return Response({
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
        graphite_render_host = settings.PLUGINS_CONFIG.get('sidekick', {}).get('graphite_render_host', None)
        if graphite_render_host is None:
            return Response({})

        (services_in, services_out) = utils.format_graphite_service_query(services)
        service_data = utils.get_graphite_data(graphite_render_host, [services_in], [services_out], period)

        accounting_data = None
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
            queries['remaining_data'] = remaining_data['query']

        return Response({
            'graph_data': graph_data,
            'queries': queries,
        })
