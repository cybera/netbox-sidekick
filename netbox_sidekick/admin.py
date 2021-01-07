from django import forms
from django.contrib import admin

from .models import (
    ContactType, Contact,

    LogicalSystem, RoutingType,
    NetworkServiceConnectionType, NetworkServiceConnection,

    MemberContact,

    NIC,
)


@admin.register(ContactType)
class ContactTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')


@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = (
        'first_name', 'last_name', 'title',
        'email', 'phone', 'comments'
    )


@admin.register(LogicalSystem)
class LogicalSystemADmin(admin.ModelAdmin):
    list_display = ('name', 'slug')


@admin.register(MemberContact)
class MemberContactAdmin(admin.ModelAdmin):
    list_display = (
        'member', 'contact', 'type'
    )


@admin.register(NetworkServiceConnectionType)
class NetworkServiceConnectionTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')


class NetworkServiceConnectionAdminForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['interface'].widget = forms.TextInput()
        self.fields['provider_router_address_ipv4'].widget = forms.TextInput()
        self.fields['member_router_address_ipv4'].widget = forms.TextInput()
        self.fields['provider_router_address_ipv6'].widget = forms.TextInput()
        self.fields['member_router_address_ipv6'].widget = forms.TextInput()

    class Meta:
        model = NetworkServiceConnection
        fields = []


@admin.register(NetworkServiceConnection)
class NetworkServiceAdminConnection(admin.ModelAdmin):
    form = NetworkServiceConnectionAdminForm
    fieldsets = (
        ('Tenant', {
            'fields': ('tenant',),
        }),

        ('General', {
            'fields': (
                'name', 'network_service_connection_type', 'description',
                'comments', 'active', 'start_date', 'end_date',),
        }),

        ('Configuration', {
            'fields': (
                'device', 'interface', 'logical_system',
                'routing_type', 'asn'),
        }),

        ('IPv4 Information', {
            'fields': (
                'ipv4_unicast', 'ipv4_nunicast',
                'provider_router_address_ipv4', 'member_router_address_ipv4',
                'ipv4_prefixes',),
        }),

        ('IPv6 Information', {
            'fields': (
                'ipv6_unicast', 'ipv6_nunicast',
                'provider_router_address_ipv6', 'member_router_address_ipv6',
                'ipv6_prefixes',),
        }),
    )


@admin.register(NIC)
class NICAdmin(admin.ModelAdmin):
    fieldsets = (
        ('Interface', {
            'fields': ('interface',),
        }),

        ('Status', {
            'fields': ('admin_status', 'oper_status',),
        }),

        ('Counters', {
            'fields': (
                'out_octets', 'in_octets', 'out_unicast_packets', 'in_unicast_packets',
                'out_nunicast_packets', 'in_nunicast_packets',
                'out_errors', 'in_errors',
            ),
        }),
    )


@admin.register(RoutingType)
class RoutingTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
