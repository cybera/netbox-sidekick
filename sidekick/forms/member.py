import datetime

from django import forms

from django.contrib.auth.models import Group
from django.utils.text import slugify

from tenancy.models import Tenant

from dcim.models import Site, Device

from sidekick.models import (
    LogicalSystem,
    NetworkServiceType, NetworkService,
    NetworkServiceDevice, NetworkServiceL3,
    RoutingType,
)

from sidekick.utils import MEMBER_TYPE_CHOICES


class MemberCreateForm(forms.Form):
    date_widget = forms.DateInput(
        attrs={
            "class": "form-control mt-0",
            "type": "date",
            "value": datetime.date.today,
        }
    )

    member_name = forms.CharField(
        label='Member Name',
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control'}))

    member_type = forms.ChoiceField(
        label='Member Type',
        required=True,
        choices=MEMBER_TYPE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'}))

    latitude = forms.CharField(
        label="Latitude",
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control'}))

    longitude = forms.CharField(
        label="Longitude",
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control'}))

    network_service_name = forms.CharField(
        label="Network Service Name",
        required=True,
        help_text='Example: "Calgary - Primary"',
        widget=forms.TextInput(attrs={'class': 'form-control'}))

    network_service_type = forms.ModelChoiceField(
        label="Network Service Type",
        required=True,
        queryset=NetworkServiceType.objects.distinct(),
        widget=forms.Select(attrs={'class': 'netbox-select2-static form-control'}))

    network_service_description = forms.CharField(
        label='Network Service Description',
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'}))

    start_date = forms.DateField(
        label='Start Date',
        required=False,
        initial=datetime.date.today,
        widget=date_widget)

    backup_service = forms.ModelChoiceField(
        label="Backup Service for",
        required=False,
        queryset=NetworkService.objects.distinct(),
        help_text="The primary service",
        widget=forms.Select(attrs={'class': 'netbox-select2-static form-control'}))

    device = forms.ModelChoiceField(
        label="Device",
        required=True,
        queryset=Device.objects.filter(name__icontains="router").distinct(),
        help_text='Router  where the member connects to us',
        widget=forms.Select(attrs={'class': 'netbox-select2-static form-control'}))

    interface = forms.CharField(
        label='Device Interface',
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'}))

    vlan = forms.CharField(
        label='VLAN',
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'}))

    network_device_comments = forms.CharField(
        label='Comments',
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'}))

    logical_system = forms.ModelChoiceField(
        label="Logical System",
        required=True,
        queryset=LogicalSystem.objects.distinct(),
        widget=forms.Select(attrs={'class': 'netbox-select2-static form-control'}))

    routing_type = forms.ModelChoiceField(
        label="Routing Type",
        required=True,
        queryset=RoutingType.objects.distinct(),
        widget=forms.Select(attrs={'class': 'netbox-select2-static form-control'}))

    asn = forms.CharField(
        label='ASN',
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'}))

    ipv4_unicast = forms.BooleanField(
        label='IPv4 Unicast?',
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'netbox-select2-static'}))

    ipv4_multicast = forms.BooleanField(
        label='IPv4 Multicast?',
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'netbox-select2-static'}))

    provider_router_address_ipv4 = forms.CharField(
        label='Provider Router IPv4 Address',
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'}))

    member_router_address_ipv4 = forms.CharField(
        label='Member Router IPv4 Address',
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'}))

    ipv6_unicast = forms.BooleanField(
        label='IPv6 Unicast?',
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'netbox-select2-static'}))

    ipv6_multicast = forms.BooleanField(
        label='IPv6 Multicast?',
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'netbox-select2-static'}))

    provider_router_address_ipv6 = forms.CharField(
        label='Provider Router IPv6 Address',
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'}))

    member_router_address_ipv6 = forms.CharField(
        label='Member Router IPv6 Address',
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'}))

    ipv4_prefixes = forms.CharField(
        label='IPv4 Prefixes',
        help_text="Enter one per line",
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control'}))

    ipv6_prefixes = forms.CharField(
        label='IPv6 Prefixes',
        help_text="Enter one per line",
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control'}))

    def clean_member_name(self):
        member_name = self.cleaned_data["member_name"]
        existing_member = Tenant.objects.filter(name__iexact=member_name)
        if len(existing_member) > 0:
            self.add_error("member_name", "Member already exists")

        existing_group = Group.objects.filter(name__iexact=member_name)
        if len(existing_group) > 0:
            self.add_error("member_name", "A group with the same name already exists")

        existing_site = Site.objects.filter(name__iexact=member_name)
        if len(existing_site) > 0:
            self.add_error("member_name", f"A site with the same name already exists: {existing_site[0]}")

        return member_name

    def clean_interface(self):
        device = self.cleaned_data["device"]
        interface_name = self.cleaned_data["interface"]
        existing_interfaces = []
        for i in device.vc_interfaces():
            existing_interfaces.append(i.name)

        if interface_name not in existing_interfaces:
            self.add_error("interface", "Interface does not exist on the device")

    def create_member(self):
        member_name = self.cleaned_data["member_name"]
        member_type = self.cleaned_data["member_type"]
        latitude = self.cleaned_data["latitude"]
        longitude = self.cleaned_data["longitude"]

        tenant = Tenant.objects.create(
            name=member_name,
            slug=slugify(member_name),
        )
        tenant.cf["member_type"] = member_type
        tenant.save()

        site = Site.objects.create(
            name=member_name,
            tenant=tenant,
            slug=slugify(member_name),
            latitude=latitude,
            longitude=longitude,
        )
        site.save()

        group = Group.objects.create(name=member_name)
        group.save()

        network_service_name = self.cleaned_data["network_service_name"]
        network_service_type = self.cleaned_data["network_service_type"]
        network_service_desc = self.cleaned_data["network_service_description"]
        start_date = self.cleaned_data["start_date"]
        backup_service = self.cleaned_data["backup_service"]

        network_service = NetworkService.objects.create(
            name=network_service_name,
            network_service_type=network_service_type,
            description=network_service_desc,
            member=tenant,
            member_site=site,
            start_date=start_date,
            backup_for=backup_service,
        )
        network_service.save()

        device = self.cleaned_data["device"]
        interface = self.cleaned_data["interface"]
        vlan = self.cleaned_data["vlan"]
        network_device_comments = self.cleaned_data["network_device_comments"]

        network_service_device = NetworkServiceDevice.objects.create(
            network_service=network_service,
            device=device,
            interface=interface,
            vlan=vlan,
            comments=network_device_comments,
        )
        network_service_device.save()

        logical_system = self.cleaned_data["logical_system"]
        routing_type = self.cleaned_data["routing_type"]
        asn = self.cleaned_data["asn"]
        ipv4_unicast = self.cleaned_data["ipv4_unicast"]
        ipv4_multicast = self.cleaned_data["ipv4_multicast"]
        ipv4_prefixes = self.cleaned_data["ipv4_prefixes"]
        ipv6_unicast = self.cleaned_data["ipv6_unicast"]
        ipv6_multicast = self.cleaned_data["ipv6_multicast"]
        ipv6_prefixes = self.cleaned_data["ipv6_prefixes"]
        provider_router_address_ipv4 = self.cleaned_data["provider_router_address_ipv4"]
        member_router_address_ipv4 = self.cleaned_data["member_router_address_ipv4"]
        provider_router_address_ipv6 = self.cleaned_data["provider_router_address_ipv6"]
        member_router_address_ipv6 = self.cleaned_data["member_router_address_ipv6"]

        network_service_l3 = NetworkServiceL3.objects.create(
            network_service_device=network_service_device,
            logical_system=logical_system,
            routing_type=routing_type,
            asn=asn,
            ipv4_unicast=ipv4_unicast,
            ipv4_multicast=ipv4_multicast,
            ipv4_prefixes=ipv4_prefixes,
            ipv6_unicast=ipv6_unicast,
            ipv6_multicast=ipv6_multicast,
            ipv6_prefixes=ipv6_prefixes,
            provider_router_address_ipv4=provider_router_address_ipv4,
            member_router_address_ipv4=member_router_address_ipv4,
            provider_router_address_ipv6=provider_router_address_ipv6,
            member_router_address_ipv6=member_router_address_ipv6,
        )
        network_service_l3.save()

        return True
