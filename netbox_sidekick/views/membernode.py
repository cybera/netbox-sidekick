from django.contrib.auth.mixins import PermissionRequiredMixin
from django.shortcuts import get_object_or_404
from django.views.generic import DetailView

from django_filters.views import FilterView
from django_tables2.views import SingleTableView

from netbox_sidekick.filters import MemberNodeTypeFilterSet, MemberNodeFilterSet
from netbox_sidekick.models import MemberNodeType, MemberNode
from netbox_sidekick.tables import MemberNodeTypeTable, MemberNodeTable


# Member Node Type Index
class MemberNodeTypeIndexView(PermissionRequiredMixin, FilterView, SingleTableView):
    permission_required = 'netbox_sidekick.view_membernodetype'
    model = MemberNodeType
    table_class = MemberNodeTypeTable
    filterset_class = MemberNodeTypeFilterSet
    template_name = 'netbox_sidekick/membernode/membernodetype_index.html'


# Member Node Type Details
class MemberNodeTypeDetailView(PermissionRequiredMixin, DetailView):
    permission_required = 'netbox_sidekick.view_membernodetype'
    model = MemberNodeType
    template_name = 'netbox_sidekick/membernode/membernodetype.html'

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


# Member Node Index
class MemberNodeIndexView(PermissionRequiredMixin, FilterView, SingleTableView):
    permission_required = 'netbox_sidekick.view_membernode'
    model = MemberNode
    table_class = MemberNodeTable
    filterset_class = MemberNodeFilterSet
    template_name = 'netbox_sidekick/membernode/membernode_index.html'


# Member Node Details
class MemberNodeDetailView(PermissionRequiredMixin, DetailView):
    permission_required = 'netbox_sidekick.view_membernode'
    model = MemberNode
    template_name = 'netbox_sidekick/membernode/membernode.html'
