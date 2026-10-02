from django import forms
from django.forms import inlineformset_factory

from netbox.forms import NetBoxModelForm

from utilities.forms.widgets import DatePicker

from sidekick.models import (
    LogicalSystem,
    NetworkService,
    NetworkServiceDevice,
    NetworkServiceGroup,
    NetworkServiceL2,
    NetworkServiceL3,
    NetworkServiceType,
    RoutingType,
)


class LogicalSystemForm(NetBoxModelForm):
    class Meta:
        model = LogicalSystem
        fields = ('name',)


class RoutingTypeForm(NetBoxModelForm):
    class Meta:
        model = RoutingType
        fields = ('name',)


class NetworkServiceTypeForm(NetBoxModelForm):
    class Meta:
        model = NetworkServiceType
        fields = ('name',)


class NetworkServiceForm(NetBoxModelForm):
    start_date = forms.DateTimeField(
        required=True,
        label="Start Date",
        widget=DatePicker,
    )

    class Meta:
        model = NetworkService
        fields = ('name', 'network_service_type', 'member', 'member_site', 'legacy_id',
                  'start_date', 'end_date', 'description', 'comments', 'active',
                  'backup_for', 'accounting_profile',)


class NetworkServiceL2InlineForm(forms.ModelForm):
    """
    A single editable row in the L2 Services inline on the NetworkServiceDevice
    form.

    Deliberately a plain ModelForm rather than a NetBoxModelForm (see
    BandwidthProfileInlineForm in sidekick.forms.accounting): the inline renders
    as a compact table, and NetBoxModelForm would add a per-row tag widget and
    custom-field inputs to every line.
    """
    class Meta:
        model = NetworkServiceL2
        fields = ('vlan', 'comments')


class NetworkServiceL3InlineForm(forms.ModelForm):
    """
    A single editable row in the L3 Services inline on the NetworkServiceDevice
    form. Field set mirrors the removed Django admin's NetworkServiceL3 inline:
    member/member_site/ip_prefixes/active stay on the standalone L3 page.
    """
    class Meta:
        model = NetworkServiceL3
        fields = (
            'logical_system', 'routing_type', 'asn',
            'ipv4_unicast', 'ipv4_multicast',
            'provider_router_address_ipv4', 'member_router_address_ipv4',
            'ipv6_unicast', 'ipv6_multicast',
            'provider_router_address_ipv6', 'member_router_address_ipv6',
            'comments',
        )


# The inline formsets that replace the Django admin's NetworkServiceL2/L3
# inlines, which were removed with the admin in NetBox 4 (see ADR-064).
NetworkServiceL2FormSet = inlineformset_factory(
    NetworkServiceDevice,
    NetworkServiceL2,
    form=NetworkServiceL2InlineForm,
    extra=1,
    can_delete=True,
    can_delete_extra=False,
)

NetworkServiceL3FormSet = inlineformset_factory(
    NetworkServiceDevice,
    NetworkServiceL3,
    form=NetworkServiceL3InlineForm,
    extra=1,
    can_delete=True,
    can_delete_extra=False,
)


class NetworkServiceDeviceForm(NetBoxModelForm):
    """
    NetworkServiceDevice form carrying the L2 and L3 inline formsets.

    Same form-owned-formset pattern as AccountingProfileForm (ADR-073): the
    generic ObjectEditView has no formset support, so both formsets are built
    in __init__(), validated in clean() and saved in save(). Validation is
    coupled on purpose -- an invalid inline row makes the whole form invalid
    and the view re-renders instead of saving a partial edit.
    """
    class Meta:
        model = NetworkServiceDevice
        fields = ('network_service', 'device', 'interface', 'vlan', 'comments', 'legacy_id',)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.l2_formset = NetworkServiceL2FormSet(
            data=self.data if self.is_bound else None,
            files=self.files if self.is_bound else None,
            instance=self.instance,
            prefix='network_service_l2',
        )
        self.l3_formset = NetworkServiceL3FormSet(
            data=self.data if self.is_bound else None,
            files=self.files if self.is_bound else None,
            instance=self.instance,
            prefix='network_service_l3',
        )

    def clean(self):
        cleaned_data = super().clean()
        errors = []
        if not self.l3_formset.is_valid():
            errors.append(forms.ValidationError(
                'Correct the errors in the L3 services below.'))
        if not self.l2_formset.is_valid():
            errors.append(forms.ValidationError(
                'Correct the errors in the L2 services below.'))
        if errors:
            raise forms.ValidationError(errors)
        return cleaned_data

    def save(self, commit=True):
        obj = super().save(commit=commit)
        if commit:
            # The parent must exist before its inline rows can point at it,
            # so the formsets are saved after the device itself.
            self.l2_formset.instance = obj
            self.l3_formset.instance = obj
            self.l3_formset.save()
            self.l2_formset.save()
        return obj


class NetworkServiceL2Form(NetBoxModelForm):
    class Meta:
        model = NetworkServiceL2
        fields = ('network_service_device', 'vlan', 'comments', 'legacy_id',)


class NetworkServiceL3Form(NetBoxModelForm):
    class Meta:
        model = NetworkServiceL3
        fields = ('member', 'member_site',
                  'network_service_device', 'logical_system', 'routing_type', 'asn',
                  'ip_prefixes',
                  'ipv4_unicast', 'ipv4_multicast',
                  'provider_router_address_ipv4', 'member_router_address_ipv4',
                  'ipv6_unicast', 'ipv6_multicast',
                  'provider_router_address_ipv6', 'member_router_address_ipv6',
                  'comments', 'legacy_id', 'active',)


class NetworkServiceGroupForm(NetBoxModelForm):
    class Meta:
        model = NetworkServiceGroup
        fields = ('name', 'slug', 'description', 'network_services',)
