from django.contrib.auth.mixins import PermissionRequiredMixin
from django.shortcuts import get_object_or_404
from django.views.generic import DetailView

from django_filters.views import FilterView
from django_tables2.views import SingleTableView

from netbox_sidekick.filters import MemberNodeLinkTypeFilterSet, MemberNodeLinkFilterSet
from netbox_sidekick.models import MemberNodeLinkType, MemberNodeLink
from netbox_sidekick.tables import MemberNodeLinkTypeTable, MemberNodeLinkTable


# Member Node Link Type Index
class MemberNodeLinkTypeIndexView(PermissionRequiredMixin, FilterView, SingleTableView):
    permission_required = 'netbox_sidekick.view_membernodelinktype'
    model = MemberNodeLinkType
    table_class = MemberNodeLinkTypeTable
    filterset_class = MemberNodeLinkTypeFilterSet
    template_name = 'netbox_sidekick/membernodelink/membernodelinktype_index.html'


# Member Node Link Type Details
class MemberNodeLinkTypeDetailView(PermissionRequiredMixin, DetailView):
    permission_required = 'netbox_sidekick.view_membernodelinktype'
    model = MemberNodeLinkType
    template_name = 'netbox_sidekick/membernodelink/membernodelinktype.html'

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
    template_name = 'netbox_sidekick/membernodelink/membernodelink_index.html'


# Member Node Link Details
class MemberNodeLinkDetailView(PermissionRequiredMixin, DetailView):
    permission_required = 'netbox_sidekick.view_membernodelink'
    model = MemberNodeLink
    template_name = 'netbox_sidekick/membernodelink/membernodelink.html'
