from django import forms
from django.forms import inlineformset_factory

from netbox.forms import NetBoxModelForm
from sidekick.models import (
    AccountingProfile,
    AccountingSource,
    BandwidthProfile,
)


class BandwidthProfileInlineForm(forms.ModelForm):
    """
    A single editable row in the Bandwidth Profiles inline on the
    AccountingProfile form.

    Deliberately a plain ModelForm rather than a NetBoxModelForm: the inline
    renders as a compact table, and NetBoxModelForm would add a per-row tag
    widget and custom-field inputs to every line. Tags and custom fields on a
    BandwidthProfile remain editable through its own object pages.
    """
    class Meta:
        model = BandwidthProfile
        fields = ('effective_date', 'traffic_cap', 'burst_limit', 'billable', 'comments')


# The inline formset that replaces the Django admin's BandwidthProfileInline,
# which was removed with the admin in NetBox 4 (see ADR-064).
BandwidthProfileFormSet = inlineformset_factory(
    AccountingProfile,
    BandwidthProfile,
    form=BandwidthProfileInlineForm,
    extra=1,
    can_delete=True,
    can_delete_extra=False,
)


class AccountingProfileForm(NetBoxModelForm):
    """
    AccountingProfile form carrying an inline BandwidthProfile formset.

    NetBox 4.7's generic ObjectEditView has no formset support, so the formset
    is owned by the form: built in __init__(), validated in clean(), saved in
    save(). That keeps the generic edit view -- and its permissions, changelog
    handling and redirects -- completely untouched.

    Validation is coupled on purpose: if any inline row is invalid, clean()
    raises, so the whole form is invalid and ObjectEditView re-renders instead
    of saving a partially-edited profile.
    """
    class Meta:
        model = AccountingProfile
        fields = ('member', 'name', 'enabled', 'comments', 'accounting_sources')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.formset = BandwidthProfileFormSet(
            data=self.data if self.is_bound else None,
            files=self.files if self.is_bound else None,
            instance=self.instance,
            prefix='bandwidth_profiles',
        )

    def clean(self):
        cleaned_data = super().clean()
        if not self.formset.is_valid():
            raise forms.ValidationError(
                'Correct the errors in the bandwidth profiles below.'
            )
        return cleaned_data

    def save(self, commit=True):
        obj = super().save(commit=commit)
        if commit:
            # The parent must exist before its inline rows can point at it,
            # so the formset is saved after the profile itself.
            self.formset.instance = obj
            self.formset.save()
        return obj


class AccountingSourceForm(NetBoxModelForm):
    class Meta:
        model = AccountingSource
        fields = ('device', 'name', 'destination',)


class BandwidthProfileForm(NetBoxModelForm):
    class Meta:
        model = BandwidthProfile
        # billable was omitted here, although the model has it and the removed
        # admin inline exposed it. Restored so the standalone form can set it.
        fields = (
            'accounting_profile', 'effective_date', 'comments',
            'traffic_cap', 'burst_limit', 'billable',
        )
