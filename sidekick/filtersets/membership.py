import django_filters

from django import forms
from django.contrib.auth import get_user_model
from django.db.models import Q

from netbox.filtersets import NetBoxModelFilterSet
from netbox.forms import NetBoxModelFilterSetForm
from tenancy.models import Tenant
from utilities.forms.fields import DynamicModelMultipleChoiceField, TagFilterField

from sidekick.models import MemberTenant


class MemberTenantFilterSet(NetBoxModelFilterSet):
    user_id = django_filters.ModelMultipleChoiceFilter(
        field_name='user',
        queryset=get_user_model().objects.all(),
        label='Account (ID)',
    )
    tenant_id = django_filters.ModelMultipleChoiceFilter(
        field_name='tenant',
        queryset=Tenant.objects.filter(group__name='Members'),
        label='Member (ID)',
    )
    role = django_filters.ChoiceFilter(choices=MemberTenant.ROLE_CHOICES)

    class Meta:
        model = MemberTenant
        fields = ('role', 'user_id', 'tenant_id')

    def search(self, queryset, name, value):
        if not value.strip():
            return queryset
        return queryset.filter(
            Q(user__username__icontains=value) |
            Q(user__email__icontains=value) |
            Q(tenant__name__icontains=value) |
            Q(note__icontains=value)
        )


class MemberTenantFilterSetForm(NetBoxModelFilterSetForm):
    model = MemberTenant

    fieldsets = (
        (None, ('q', 'filter_id', 'tag')),
        ('Entitlement', ('user_id', 'tenant_id', 'role')),
    )

    user_id = DynamicModelMultipleChoiceField(
        queryset=get_user_model().objects.all(),
        required=False,
        label='Account',
    )
    tenant_id = DynamicModelMultipleChoiceField(
        queryset=Tenant.objects.filter(group__name='Members'),
        required=False,
        label='Member',
    )
    role = forms.ChoiceField(
        choices=MemberTenant.ROLE_CHOICES,
        required=False,
        label='Role',
    )
    tag = TagFilterField(model)
