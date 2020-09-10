from django.contrib.auth.mixins import PermissionRequiredMixin
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.views.generic import DetailView

from django_filters.views import FilterView
from django_tables2.views import SingleTableView

from netbox_sidekick.filters import MemberTypeFilterSet, MemberFilterSet

from netbox_sidekick.models import (
    Contact,
    MemberType, Member,
    MemberNode,
    MemberNodeLink,
    NetworkServiceConnection,
)

from netbox_sidekick.tables import (
    ContactTable,
    MemberTypeTable, MemberTable,
    MemberNodeTable,
    MemberNodeLinkTable,
    NetworkServiceConnectionTable,
)


# Member Type Index
class MemberTypeIndexView(PermissionRequiredMixin, FilterView, SingleTableView):
    permission_required = 'netbox_sidekick.view_membertype'
    model = MemberType
    table_class = MemberTypeTable
    filterset_class = MemberTypeFilterSet
    template_name = 'netbox_sidekick/member/membertype_index.html'


# Member Type Details
class MemberTypeDetailView(PermissionRequiredMixin, DetailView):
    permission_required = 'netbox_sidekick.view_membertype'
    model = MemberType
    template_name = 'netbox_sidekick/member/membertype.html'

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


# Member Index
class MemberIndexView(PermissionRequiredMixin, FilterView, SingleTableView):
    permission_required = 'netbox_sidekick.view_member'
    model = Member
    table_class = MemberTable
    filterset_class = MemberFilterSet
    template_name = 'netbox_sidekick/member/member_index.html'


# Member Details
class MemberDetailView(PermissionRequiredMixin, DetailView):
    permission_required = 'netbox_sidekick.view_member'
    model = Member
    template_name = 'netbox_sidekick/member/member.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        member = get_object_or_404(
            Member, pk=self.kwargs['pk'])
        context['member'] = member

        # Build a table of all contacts that the member has.
        contacts_table = ContactTable(Contact.objects.filter(
            membercontact__member=member.id))
        context['contacts_table'] = contacts_table

        # Build a table of all services that the member has.
        services_table = NetworkServiceConnectionTable(NetworkServiceConnection.objects.filter(
            member=member.id))
        context['services_table'] = services_table

        # Build a table of all nodes that the member has.
        nodes_table = MemberNodeTable(MemberNode.objects.filter(
            owner=member.id))
        context['nodes_table'] = nodes_table

        # Build a table of all links that the member has.
        links_table = MemberNodeLinkTable(MemberNodeLink.objects.filter(
            Q(a_endpoint__owner=member.id) |
            Q(z_endpoint__owner=member.id)
        ))
        context['links_table'] = links_table

        return context
