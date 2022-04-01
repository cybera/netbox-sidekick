from django.conf import settings
from django.http import Http404

from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.renderers import JSONRenderer
from rest_framework.views import APIView

from netbox.api.authentication import TokenAuthentication

from sidekick import utils
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
        graphite_render_host = settings.PLUGINS_CONFIG['sidekick'].get('graphite_render_host', None)
        if graphite_render_host is None:
            return Response({})

        group_id = self.kwargs.get('group_id', None)
        if group_id is None:
            raise Http404

        try:
            service_group = NetworkServiceGroup.objects.get(id=group_id)
        except NetworkServiceGroup.DoesNotExist:
            raise Http404

        all_members = []
        all_services = []
        all_accounting_sources = []
        for network_service in service_group.network_services.all():
            member = network_service.member
            if member.name not in all_members:
                all_members.append(member.name)
                all_services.extend(utils.get_services(member))
                all_accounting_sources.extend(utils.get_accounting_sources(member))

        period = utils.get_period(request)
        service_data = utils.get_graphite_service_data(graphite_render_host, all_services, period)
        accounting_data = utils.get_graphite_accounting_data(graphite_render_host, all_accounting_sources, period)
        remaining_data = utils.get_graphite_remaining_data(graphite_render_host, all_services, period)

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
        graphite_render_host = settings.PLUGINS_CONFIG['sidekick'].get('graphite_render_host', None)
        if graphite_render_host is None:
            return Response({})

        member_id = self.kwargs.get('member_id', None)
        if member_id is None:
            raise Http404

        try:
            member = Tenant.objects.get(id=member_id)
        except Tenant.DoesNotExist:
            raise Http404

        services = utils.get_services(member)
        accounting_sources = utils.get_accounting_sources(member)
        period = utils.get_period(request)
        service_data = utils.get_graphite_service_data(graphite_render_host, services, period)
        accounting_data = utils.get_graphite_accounting_data(graphite_render_host, accounting_sources, period)
        remaining_data = utils.get_graphite_remaining_data(graphite_render_host, services, period)

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
