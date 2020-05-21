from django.contrib.auth.mixins import PermissionRequiredMixin
from django.shortcuts import get_object_or_404
from django.views.generic import DetailView

from django_filters.views import FilterView
from django_tables2.views import SingleTableView

from .filters import (
    MemberTypeFilterSet, MemberFilterSet,
    MemberNodeTypeFilterSet, MemberNodeFilterSet,
    MemberNodeLinkTypeFilterSet, MemberNodeLinkFilterSet,
    NetworkServiceTypeFilterSet, NetworkServiceFilterSet,
)

from .models import (
    MemberType, Member,
    MemberNodeType, MemberNode,
    MemberNodeLinkType, MemberNodeLink,
    NetworkServiceType, NetworkService,
)

from .tables import (
    MemberTypeTable, MemberTable,
    MemberNodeTypeTable, MemberNodeTable,
    MemberNodeLinkTypeTable, MemberNodeLinkTable,
    NetworkServiceTypeTable, NetworkServiceTable,
)


# Member Type Index
class MemberTypeIndexView(PermissionRequiredMixin, FilterView, SingleTableView):
    permission_required = 'netbox_sidekick.view_membertype'
    model = MemberType
    table_class = MemberTypeTable
    filterset_class = MemberTypeFilterSet
    template_name_suffix = '_index'


# Member Type Details
class MemberTypeDetailView(PermissionRequiredMixin, DetailView):
    permission_required = 'netbox_sidekick.view_membertype'
    model = MemberType
    template_name = 'netbox_sidekick/membertype.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        member_type = get_object_or_404(
            MemberType, slug=self.kwargs['slug'])
        context['member_type'] = member_type

        # Build a table of all members of a specific member type.
        table = MemberTable(Member.objects.filter(
            member_type=member_type.id))
        context['table'] = table

        return context


# Member Node Type Index
class MemberNodeTypeIndexView(PermissionRequiredMixin, FilterView, SingleTableView):
    permission_required = 'netbox_sidekick.view_membernodetype'
    model = MemberNodeType
    table_class = MemberNodeTypeTable
    filterset_class = MemberNodeTypeFilterSet
    template_name_suffix = '_index'


# Member Node Type Details
class MemberNodeTypeDetailView(PermissionRequiredMixin, DetailView):
    permission_required = 'netbox_sidekick.view_membernodetype'
    model = MemberNodeType
    template_name = 'netbox_sidekick/membernodetype.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        node_type = get_object_or_404(
            MemberNodeType, slug=self.kwargs['slug'])
        context['node_type'] = node_type

        # Build a table of all member nodes
        # of a specific node type.
        table = MemberNodeTable(MemberNode.objects.filter(
            node_type=node_type.id))
        context['table'] = table

        return context


# Member Index
class MemberIndexView(PermissionRequiredMixin, FilterView, SingleTableView):
    permission_required = 'netbox_sidekick.view_member'
    model = Member
    table_class = MemberTable
    filterset_class = MemberFilterSet
    template_name_suffix = '_index'


# Member Details
class MemberDetailView(PermissionRequiredMixin, DetailView):
    permission_required = 'netbox_sidekick.view_member'
    model = Member
    template_name = 'netbox_sidekick/member.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        member = get_object_or_404(
            Member, pk=self.kwargs['pk'])
        context['member'] = member

        # Build a table of all services that the member has.
        table = NetworkServiceTable(NetworkService.objects.filter(
            member=member.id))
        context['table'] = table

        return context


# Member Node Index
class MemberNodeIndexView(PermissionRequiredMixin, FilterView, SingleTableView):
    permission_required = 'netbox_sidekick.view_membernode'
    model = MemberNode
    table_class = MemberNodeTable
    filterset_class = MemberNodeFilterSet
    template_name_suffix = '_index'


# Member Node Details
class MemberNodeDetailView(PermissionRequiredMixin, DetailView):
    permission_required = 'netbox_sidekick.view_membernode'
    model = MemberNode
    template_name = 'netbox_sidekick/membernode.html'


# Member Node Link Type Index
class MemberNodeLinkTypeIndexView(PermissionRequiredMixin, FilterView, SingleTableView):
    permission_required = 'netbox_sidekick.view_membernodelinktype'
    model = MemberNodeLinkType
    table_class = MemberNodeLinkTypeTable
    filterset_class = MemberNodeLinkTypeFilterSet
    template_name_suffix = '_index'


# Member Node Link Type Details
class MemberNodeLinkTypeDetailView(PermissionRequiredMixin, DetailView):
    permission_required = 'netbox_sidekick.view_membernodelinktype'
    model = MemberNodeLinkType
    template_name = 'netbox_sidekick/membernodelinktype.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        link_type = get_object_or_404(
            MemberNodeLinkType, slug=self.kwargs['slug'])
        context['link_type'] = link_type

        # Build a table of all member nodes
        # of a specific node type.
        table = MemberNodeLinkTable(MemberNodeLink.objects.filter(
            link_type=link_type.id))
        context['table'] = table

        return context


# Member Node Link Index
class MemberNodeLinkIndexView(PermissionRequiredMixin, FilterView, SingleTableView):
    permission_required = 'netbox_sidekick.view_membernodelink'
    model = MemberNodeLink
    table_class = MemberNodeLinkTable
    filterset_class = MemberNodeLinkFilterSet
    template_name_suffix = '_index'


# Member Node Link Details
class MemberNodeLinkDetailView(PermissionRequiredMixin, DetailView):
    permission_required = 'netbox_sidekick.view_membernodelink'
    model = MemberNodeLink
    template_name = 'netbox_sidekick/membernodelink.html'


# Network Service Type Index
class NetworkServiceTypeIndexView(PermissionRequiredMixin, FilterView, SingleTableView):
    permission_required = 'netbox_sidekick.view_networkservicetype'
    model = NetworkServiceType
    table_class = NetworkServiceTypeTable
    filterset_class = NetworkServiceTypeFilterSet
    template_name_suffix = '_index'


# Network Service Type Details
class NetworkServiceTypeDetailView(PermissionRequiredMixin, DetailView):
    permission_required = 'netbox_sidekick.view_networkservicetype'
    model = NetworkServiceType
    template_name = 'netbox_sidekick/networkservicetype.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        nst = get_object_or_404(NetworkServiceType, slug=self.kwargs['slug'])
        context['nst'] = nst

        table = NetworkServiceTable(NetworkService.objects.filter(
            network_service_type=nst.id))
        context['table'] = table

        return context


# Network Service Index
class NetworkServiceIndexView(PermissionRequiredMixin, FilterView, SingleTableView):
    permission_required = 'netbox_sidekick.view_networkservice'
    model = NetworkService
    table_class = NetworkServiceTable
    filterset_class = NetworkServiceFilterSet
    template_name_suffix = '_index'


# Network Service Details
class NetworkServiceDetailView(PermissionRequiredMixin, DetailView):
    permission_required = 'netbox_sidekick.view_networkservice'
    model = NetworkService
    context_object_name = 'ns'
    template_name = 'netbox_sidekick/networkservice.html'
