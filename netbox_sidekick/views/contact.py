from django.contrib.auth.mixins import PermissionRequiredMixin
from django.shortcuts import get_object_or_404
from django.views.generic import DetailView

from django_filters.views import FilterView
from django_tables2.views import SingleTableView

from netbox_sidekick.filters import ContactTypeFilterSet, ContactFilterSet
from netbox_sidekick.models import ContactType, Contact, Member
from netbox_sidekick.tables import ContactTypeTable, ContactTable, MemberTable


# Contact Type Index
class ContactTypeIndexView(PermissionRequiredMixin, FilterView, SingleTableView):
    permission_required = 'netbox_sidekick.view_contacttype'
    model = ContactType
    table_class = ContactTypeTable
    filterset_class = ContactTypeFilterSet
    template_name = 'netbox_sidekick/contact/contacttype_index.html'


# Contact Type Details
class ContactTypeDetailView(PermissionRequiredMixin, DetailView):
    permission_required = 'netbox_sidekick.view_contacttype'
    model = ContactType
    template_name = 'netbox_sidekick/contact/contacttype.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        contact_type = get_object_or_404(
            ContactType, slug=self.kwargs['slug'])
        context['contact_type'] = contact_type

        # Build a table of all contacts of a specific contacts type.
        table = ContactTable(Contact.objects.filter(
            membercontact__type=contact_type.id))
        context['table'] = table

        return context


# Contact Index
class ContactIndexView(PermissionRequiredMixin, FilterView, SingleTableView):
    permission_required = 'netbox_sidekick.view_contact'
    model = Contact
    table_class = ContactTable
    filterset_class = ContactFilterSet
    template_name = 'netbox_sidekick/contact/contact_index.html'


# Contact Details
class ContactDetailView(PermissionRequiredMixin, DetailView):
    permission_required = 'netbox_sidekick.view_contact'
    model = Contact
    template_name = 'netbox_sidekick/contact/contact.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        contact = get_object_or_404(
            Contact, pk=self.kwargs['pk'])
        context['contact'] = contact

        # Build a table of all members that the contact is part of.
        table = MemberTable(Member.objects.filter(
            membercontact__contact=contact.id))
        context['table'] = table

        return context
