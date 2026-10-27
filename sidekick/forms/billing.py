from netbox.forms import NetBoxModelForm

from tenancy.models import Tenant
from utilities.forms.fields import DynamicModelChoiceField

from sidekick.models import TransitRate

# Fields that record what was agreed for a period. They are fixed once the row
# exists; a new price or start date is a new row (Clone the rate, then set the date
# and value on the copy).
CREATE_ONLY_FIELDS = ('rate_per_mbit', 'effective_date', 'comments')

FIXED_HELP_TEXT = 'Fixed when this row was created. Clone the rate to set a new price or date.'


class TransitRateForm(NetBoxModelForm):
    """Create a rate row, or correct which member an existing row belongs to.

    The member field is optional on purpose. Leaving it blank edits the global
    default rate, which is the row every member without an override falls back to.

    On an existing row only the member is editable. `resolve_transit_rate()` answers
    "what did this member pay on that date" by reading these rows, so changing a
    price or an effective date in place would silently rewrite a past bill. Django
    drops disabled fields from the submitted data, so a hand-crafted POST cannot
    change them either.
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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            for name in CREATE_ONLY_FIELDS:
                self.fields[name].disabled = True
                self.fields[name].help_text = FIXED_HELP_TEXT
