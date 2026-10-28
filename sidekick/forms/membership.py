from netbox.forms import NetBoxModelForm, NetBoxModelImportForm
from tenancy.models import Tenant
from users.models import User
from utilities.forms.fields import CommentField, DynamicModelChoiceField
from utilities.forms.rendering import FieldSet

from sidekick.models import MemberTenant


class MemberTenantForm(NetBoxModelForm):
    """Grant one account access to one member.

    The account is chosen by address because that is what the person signs in with, and
    it is what the resolver looks up. The member list is restricted to the Members tenant
    group: an entitlement to a non-member tenant would be a grant nobody can use.
    """

    user = DynamicModelChoiceField(
        queryset=User.objects.all(),
        label='Account',
        query_params={'is_active': 'true'},
        help_text='Search by address; the account must already exist',
    )
    tenant = DynamicModelChoiceField(
        queryset=Tenant.objects.filter(group__name='Members'),
        label='Member',
    )
    comments = CommentField()

    fieldsets = (
        FieldSet('user', 'tenant', 'role', 'note', name='Entitlement'),
    )

    class Meta:
        model = MemberTenant
        fields = ('user', 'tenant', 'role', 'note', 'tags')


class MemberTenantImportForm(NetBoxModelImportForm):
    class Meta:
        model = MemberTenant
        fields = ('user', 'tenant', 'role', 'note')
