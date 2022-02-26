from django.contrib.auth.mixins import PermissionRequiredMixin
from django.views.generic.edit import FormView

from sidekick.forms import (
    MemberCreateForm,
)


class MemberCreateView(PermissionRequiredMixin, FormView):
    permission_required = 'sidekick.create_member'
    template_name = 'sidekick/member/member_create.html'
    form_class = MemberCreateForm
    success_url = 'create'

    def form_valid(self, form):
        return super().form_valid(form)
