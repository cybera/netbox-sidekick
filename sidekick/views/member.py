from django.contrib.auth.mixins import PermissionRequiredMixin

from django_tables2.views import SingleTableView

from tenancy.models import Tenant
from tenancy.models import ContactRole

from sidekick.tables import (
    MemberContactTable,
)

from sidekick.models import (
    NetworkService, NetworkServiceGroup
)


class MemberContactsView(PermissionRequiredMixin, SingleTableView):
    permission_required = 'sidekick.view_networkservice'
    model = NetworkService
    template_name = 'sidekick/membercontact_list.html'

    def get_context_data(self, **kwargs):
        contacts = []
        members = []
        member_id = self.request.GET.get('member', "")

        network_service_groups = NetworkServiceGroup.objects.all()
        network_service_group_id = self.request.GET.get('network_service_group', "")
        if network_service_group_id != "":
            network_service_group_id = int(network_service_group_id)

        contact_role = None
        contact_roles = ContactRole.objects.all()
        contact_role_id = self.request.GET.get('contact_role', "")
        if contact_role_id != "":
            contact_role_id = int(contact_role_id)
            contact_role = ContactRole.objects.get(pk=contact_role_id)
        else:
            # .first() does not raise DoesNotExist, so a database with no Network
            # role used to crash here on `contact_role.id`. Fall back to the default
            # role only when it exists.
            contact_role = ContactRole.objects.filter(name="Network").first()
            if contact_role is not None:
                contact_role_id = contact_role.id

        member_names = []
        if network_service_group_id != "":
            network_service_group = NetworkServiceGroup.objects.get(pk=network_service_group_id)
            for network_service in network_service_group.network_services.all():
                if network_service.member.name not in member_names:
                    member_names.append(network_service.member.name)

        context = super().get_context_data(**kwargs)
        for member in Tenant.objects.filter(group__name="Members"):
            mid = f"{member.id}"
            if 'active' in member.cf and member.cf['active'] is False:
                continue
            members.append({'id': mid, 'name': member.name})
            if member_id != "" and member_id != mid:
                continue
            if len(member_names) > 0 and member.name not in member_names:
                continue

            # Get the portal accounts entitled to this member, but only if no
            # contact role was specified or if the Network role is specified (which
            # it is by default). Entitlement is now an explicit row rather than a
            # group whose name happens to equal the member's, so an account whose
            # group name had drifted appears here instead of silently going missing.
            if contact_role is None or contact_role.name == "Network":
                for row in member.member_tenants.select_related('user').all():
                    user = row.user
                    if user.is_active:
                        if not any(v.get('contact', None) == user.username for v in contacts):
                            contacts.append({'contact': user.username})

            # Get the contact objects from the member's sites
            # And only of the "role" specified.
            for site in member.sites.all():
                for c in site.contacts.all():
                    if site.status != "active":
                        continue
                    if not any(v.get('contact', None) == c.contact.email for v in contacts):
                        if contact_role is not None and c.role == contact_role:
                            contacts.append({'contact': c.contact.email})

        context['member_contacts'] = MemberContactTable(contacts)
        context['members'] = members
        context['network_service_groups'] = network_service_groups
        context['contact_roles'] = contact_roles
        context['selected_member'] = member_id
        context['selected_network_service_group'] = network_service_group_id
        context['selected_contact_role_id'] = contact_role_id

        return context
