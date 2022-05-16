from django.contrib.auth.mixins import PermissionRequiredMixin
from django.contrib.auth.models import Group
from django.views.generic.edit import FormView

from django_tables2.views import SingleTableView

from tenancy.models import Tenant

from sidekick.tables import (
    MemberContactTable,
)

from sidekick.forms import (
    MemberCreateForm,
)

from sidekick.models import (
    NetworkService, NetworkServiceGroup
)


class MemberCreateView(PermissionRequiredMixin, FormView):
    permission_required = 'sidekick.create_member'
    template_name = 'sidekick/member/member_create.html'
    form_class = MemberCreateForm
    success_url = 'create'

    def form_valid(self, form):
        return super().form_valid(form)


class MemberContactsView(PermissionRequiredMixin, SingleTableView):
    permission_required = 'sidekick.view_membercontacts'
    model = NetworkService
    template_name = 'sidekick/membercontact_list.html'

    def get_context_data(self, **kwargs):
        contacts = []
        members = []
        member_id = self.request.GET.get('member', "")

        network_service_groups = NetworkServiceGroup.objects.all()
        network_service_group_id = self.request.GET.get('network_service_group', "")
        member_names = []
        if network_service_group_id != "":
            network_service_group = NetworkServiceGroup.objects.get(pk=int(network_service_group_id))
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
            groups = Group.objects.filter(name__iexact=member.name)
            if len(groups) == 1:
                group = groups[0]
                for user in group.user_set.all():
                    if user.is_active:
                        if not any(v.get('contact', None) == user.username for v in contacts):
                            contacts.append({'contact': user.username})

        context['member_contacts'] = MemberContactTable(contacts)
        context['members'] = members
        context['network_service_groups'] = network_service_groups
        context['selected_member'] = member_id
        context['selected_network_service_group'] = int(network_service_group_id)

        return context
