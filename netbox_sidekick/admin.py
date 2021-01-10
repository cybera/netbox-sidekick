from django.contrib import admin

from .models import (
    ContactType, Contact,

    LogicalSystem, RoutingType, NetworkServiceType,
    NetworkService,
    NetworkServiceDevice,
    NetworkServiceL2, NetworkServiceL3,

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


@admin.register(NetworkServiceType)
class NetworkServiceTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')


@admin.register(NetworkService)
class NetworkServiceAdmin(admin.ModelAdmin):
    fieldsets = (
        ('Member', {
            'fields': ('member',),
        }),

        ('General', {
            'fields': (
                'name', 'network_service_type', 'description',
                'comments', 'active', 'start_date', 'end_date',
                'legacy_id',),
        }),
    )


@admin.register(NetworkServiceDevice)
class NetworkServiceDeviceAdmin(admin.ModelAdmin):
    fieldsets = (
        (None, {
            'fields': ('network_service',),
        }),

        ('Configuration', {
            'fields': (
                'device', 'interface', 'vlan', 'comments'),
        }),

    )


@admin.register(NetworkServiceL2)
class NetworkServiceL2Admin(admin.ModelAdmin):
    fieldsets = (
        (None, {
            'fields': (
                'network_service_device',),
        }),

        ('Configuration', {
            'fields': (
                'vlan', 'comments',),
        }),
    )


@admin.register(NetworkServiceL3)
class NetworkServiceL3Admin(admin.ModelAdmin):
    fieldsets = (
        (None, {
            'fields': (
                'network_service_device',),
        }),

        ('Configuration', {
            'fields': (
                'logical_system', 'routing_type', 'asn'),
        }),

        ('IPv4 Information', {
            'fields': (
                'ipv4_unicast', 'ipv4_multicast',
                'provider_router_address_ipv4', 'member_router_address_ipv4',
                'ipv4_prefixes',),
        }),

        ('IPv6 Information', {
            'fields': (
                'ipv6_unicast', 'ipv6_multicast',
                'provider_router_address_ipv6', 'member_router_address_ipv6',
                'ipv6_prefixes',),
        }),

        (None, {
            'fields': ('comments',),
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
