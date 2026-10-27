from netbox.forms import NetBoxModelForm

from tenancy.models import Tenant
from utilities.forms.fields import DynamicModelChoiceField

from sidekick.models import TransitRate


class TransitRateForm(NetBoxModelForm):
    """Create or edit one rate: a member override, or the global default.

    The member field is optional on purpose. Leaving it blank edits the global
    default rate, which is the row every member without an override falls back to.
    """
    tenant = DynamicModelChoiceField(
        queryset=Tenant.objects.filter(group__name='Members'),
        required=False,
        label='Member',
        help_text='Leave blank for the global default rate',
    )

    class Meta:
        model = TransitRate
        fields = ('tenant', 'rate_per_mbit', 'effective_date', 'comments')
