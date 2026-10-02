from django import forms
from django.db.models import Q
from django.forms import inlineformset_factory

from netbox.forms import NetBoxModelForm
from utilities.forms.fields import SlugField
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
    slug = SlugField()

    class Meta:
        model = LogicalSystem
        fields = ('name', 'slug')


class RoutingTypeForm(NetBoxModelForm):
    slug = SlugField()

    class Meta:
        model = RoutingType
        fields = ('name', 'slug')


class NetworkServiceTypeForm(NetBoxModelForm):
    slug = SlugField()

    class Meta:
        model = NetworkServiceType
        fields = ('name', 'slug', 'description')


class NetworkServiceDeviceRowForm(forms.ModelForm):
    """
    A single editable device row in the NetworkServiceDevice inline on the
    NetworkService form. Plain ModelForm, like the other inline rows: the
    compact table needs no per-row tags/custom-field widgets.

    legacy_id is deliberately excluded -- fields a form does not declare are
    left untouched by save(), so the legacy value survives inline edits.
    """
    class Meta:
        model = NetworkServiceDevice
        fields = ('device', 'interface', 'vlan', 'comments')


NetworkServiceDeviceFormSet = inlineformset_factory(
    NetworkService,
    NetworkServiceDevice,
    form=NetworkServiceDeviceRowForm,
    extra=1,
    can_delete=True,
    can_delete_extra=False,
)


class NetworkServiceForm(NetBoxModelForm):
    """
    NetworkService form carrying the NetworkServiceDevice inline.

    Extends the form-owned-formset pattern (ADR-073) one level further than
    NetworkServiceDeviceForm: the device formset's existing rows each carry
    their own L2 and L3 formsets (nested prefixes
    ``network_service_device-<i>-network_service_l2/l3``), so a whole
    service -- devices, VLANs and routed components -- is edited on one
    page, like the old admin's device inlines but reachable from the
    service itself.

    Constraints that keep this tractable without nested-formset support:

    * Existing device rows (with a pk) carry full L2/L3 formsets with
      nested prefixes ``network_service_device-<i>-network_service_l2/l3``
      -- add, edit and delete any number of rows.
    * A newly added device row carries one L2 row and one L3 row (plain
      forms, same nested prefix without a row index). They are created
      right after the device in the same save. If the new device needs
      more L2/L3 rows, they are added on the next save.
    * A device row marked for deletion is validated but not saved, and its
      sub-formsets are neither validated nor saved. Because
      NetworkServiceL2/L3 use on_delete=PROTECT, a device row with existing
      components is refused with an explicit error -- the user deletes the
      L2/L3 rows first, then the device (mirroring the admin's blocked
      delete).
    * The device formset's existing rows are ordered by pk so the row
      indexes -- and therefore the nested prefixes -- are identical
      between GET and POST.
    """
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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.device_formset = NetworkServiceDeviceFormSet(
            data=self.data if self.is_bound else None,
            files=self.files if self.files else None,
            instance=self.instance,
            prefix='network_service_device',
            # Existing rows ordered by pk so row indexes (and the nested
            # L2/L3 prefixes built below) are stable between GET and POST.
            queryset=(
                NetworkServiceDevice.objects.filter(network_service=self.instance)
                .order_by('pk') if self.instance.pk else None),
        )

        # Attach an L2 and L3 formset to every existing device row, with the
        # row's index baked into the nested prefix. New (extra) rows get a
        # single L2 row and a single L3 row instead: a plain form, created
        # after the device in the same save.
        for i, row in enumerate(self.device_formset.forms):
            if row.instance.pk:
                row.l2_formset = NetworkServiceL2FormSet(
                    data=self.data if self.is_bound else None,
                    files=self.files if self.files else None,
                    instance=row.instance,
                    prefix=f'network_service_device-{i}-network_service_l2',
                )
                row.l3_formset = NetworkServiceL3FormSet(
                    data=self.data if self.is_bound else None,
                    files=self.files if self.files else None,
                    instance=row.instance,
                    prefix=f'network_service_device-{i}-network_service_l3',
                )
            else:
                row.l2_form = NetworkServiceL2InlineForm(
                    data=self.data if self.is_bound else None,
                    files=self.files if self.files else None,
                    instance=NetworkServiceL2(),
                    prefix=f'network_service_device-{i}-network_service_l2',
                )
                row.l3_form = NetworkServiceL3InlineForm(
                    data=self.data if self.is_bound else None,
                    files=self.files if self.files else None,
                    instance=NetworkServiceL3(),
                    prefix=f'network_service_device-{i}-network_service_l3',
                )

    def clean(self):
        cleaned_data = super().clean()
        if not self.is_bound:
            return cleaned_data

        errors = []
        if not self.device_formset.is_valid():
            errors.append(forms.ValidationError(
                'Correct the errors in the network service devices below.'))

        # Only existing rows carry sub-formsets; new rows carry single L2/L3
        # forms. Rows marked for deletion are skipped: they are being
        # removed, and their L2/L3 rows are deleted with the device.
        for row in self.device_formset.forms:
            if row.instance.pk:
                if row.cleaned_data.get('DELETE'):
                    # NetworkServiceL2/L3 protect their device, so a device
                    # with components cannot be deleted from here -- mirror
                    # the admin's blocked-delete behaviour with an explicit
                    # error.
                    has_components = (
                        row.instance.network_service_l2.exists() or
                        row.instance.network_service_l3.exists())
                    if has_components:
                        errors.append(forms.ValidationError(
                            f'Device row {row.instance.pk} still has L2/L3 '
                            f'services. Delete those rows first.'))
                    continue
                if not row.l2_formset.is_valid():
                    errors.append(forms.ValidationError(
                        f'Correct the errors in the L2 services of device '
                        f'row {row.instance.pk}.'))
                if not row.l3_formset.is_valid():
                    errors.append(forms.ValidationError(
                        f'Correct the errors in the L3 services of device '
                        f'row {row.instance.pk}.'))
            else:
                # A new row's L2/L3 forms are only validated when the user
                # actually typed something (has_changed); an untouched extra
                # row stays out of the save entirely.
                if row.l2_form.has_changed() and not row.l2_form.is_valid():
                    errors.append(forms.ValidationError(
                        'Correct the errors in the L2 service of the new '
                        'device row.'))
                if row.l3_form.has_changed() and not row.l3_form.is_valid():
                    errors.append(forms.ValidationError(
                        'Correct the errors in the L3 service of the new '
                        'device row.'))

        if errors:
            raise forms.ValidationError(errors)
        return cleaned_data

    def save(self, commit=True):
        obj = super().save(commit=commit)
        if commit:
            # The service must exist before its device rows can point at it,
            # and each device row before its L2/L3 rows.
            self.device_formset.instance = obj
            self.device_formset.save()
            for row in self.device_formset.forms:
                if row.cleaned_data.get('DELETE'):
                    # Being deleted by the formset above; its L2/L3 rows were
                    # either deleted with it or blocked in clean().
                    continue
                if hasattr(row, 'l2_formset'):
                    # Existing device row with its L2/L3 formsets.
                    row.l3_formset.save()
                    row.l2_formset.save()
                else:
                    # A newly created device row (the formset just saved it,
                    # so it has a pk now): its single L2/L3 forms are only
                    # saved when the user typed something.
                    if row.l2_form.has_changed() and row.l2_form.is_valid():
                        row.l2_form.instance.network_service_device = row.instance
                        row.l2_form.save()
                    if row.l3_form.has_changed() and row.l3_form.is_valid():
                        row.l3_form.instance.network_service_device = row.instance
                        row.l3_form.save()
        return obj


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

        # The old Django admin filtered this dropdown to active services,
        # ordered by member name (NetworkServiceDeviceAdmin.
        # formfield_for_foreignkey). The instance's current service is kept
        # selectable so an edit of a device attached to an inactive service
        # still saves.
        if 'network_service' in self.fields:
            self.fields['network_service'].queryset = NetworkService.objects.filter(
                Q(active=True) | Q(pk=self.instance.network_service_id),
            ).order_by('member__name', 'name')

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
    # The old Django admin ordered this dropdown by member name
    # (NetworkServiceL3Admin.formfield_for_foreignkey).
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'network_service_device' in self.fields:
            self.fields['network_service_device'].queryset = (
                NetworkServiceDevice.objects
                .select_related('network_service__member', 'network_service', 'device')
                .order_by('network_service__member__name', 'network_service__name')
            )

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
    # Declared so the slug renders with NetBox's SlugWidget (auto-populate
    # from name), matching the old admin's prepopulated_fields.
    slug = SlugField()

    class Meta:
        model = NetworkServiceGroup
        fields = ('name', 'slug', 'description', 'network_services',)
