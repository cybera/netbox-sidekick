from django.contrib.auth.mixins import PermissionRequiredMixin
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
    NetworkService,
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
        member_id = self.request.GET.get('member', None)

        context = super().get_context_data(**kwargs)
        for member in Tenant.objects.filter(group__name="Members"):
            mid = f"{member.id}"
            if 'active' in member.cf and member.cf['active'] is False:
                continue
            members.append({'id': mid, 'name': member.name})
            if member_id is not None and member_id != mid:
                continue
            for site in member.sites.all():
                for c in site.contacts.all():
                    if not any(v.get('contact', None) == c.contact.email for v in contacts):
                        contacts.append({'contact': c.contact.email})

        context['member_contacts'] = MemberContactTable(contacts)
        context['members'] = members
        context['selected_member'] = member_id

        return context
