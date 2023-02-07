from django.contrib import admin

from .models import (
    AccountingProfile, AccountingSource,
    BandwidthProfile,

    LogicalSystem, RoutingType, NetworkServiceType,
    NetworkService,
    NetworkServiceDevice,
    NetworkServiceL2, NetworkServiceL3,
    NetworkServiceGroup,

    NIC,
)


class BandwidthProfileInline(admin.StackedInline):
    model = BandwidthProfile
    extra = 0

    fieldsets = (
        (None, {
            'fields': ('traffic_cap', 'burst_limit', 'effective_date'),
        }),
        (None, {
            'fields': ('comments',),
        })
    )


@admin.register(AccountingProfile)
class AccountingProfileAdmin(admin.ModelAdmin):
    inlines = (BandwidthProfileInline,)
    filter_horizontal = ('accounting_sources',)

    fieldsets = (
        (None, {
            'fields': (
                'member', 'name', 'enabled', 'comments', 'accounting_sources')
        }),
    )


@admin.register(AccountingSource)
class AccountingSourceAdmin(admin.ModelAdmin):
    list_display = (
        'device', 'name', 'destination',
    )


@admin.register(BandwidthProfile)
class BandwidthProfile(admin.ModelAdmin):
    fieldsets = (
        (None, {
            'fields': ('traffic_cap', 'burst_limit', 'effective_date'),
        }),
        (None, {
            'fields': ('comments',),
        })
    )


@admin.register(LogicalSystem)
class LogicalSystemADmin(admin.ModelAdmin):
    list_display = ('name', 'slug')


@admin.register(NetworkServiceType)
class NetworkServiceTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')


class NetworkServiceAdminActiveFilter(admin.SimpleListFilter):
    title = 'Active'
    parameter_name = 'active'

    def lookups(self, request, model_admin):
        return (
            (True, 'Yes'),
            (False, 'No'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'True':
            return queryset.filter(active=True)
        if self.value() == 'False':
            return queryset.filter(active=False)
        if self.value() == 'all':
            return queryset
        if self.value() is None:
            return queryset.filter(active=True)


@admin.register(NetworkService)
class NetworkServiceAdmin(admin.ModelAdmin):
    list_filter = (NetworkServiceAdminActiveFilter,)

    fieldsets = (
        ('Member', {
            'fields': ('member', 'member_site'),
        }),

        ('General', {
            'fields': (
                'name', 'network_service_type', 'description',
                'comments', 'active', 'start_date', 'end_date',
                'backup_for', 'accounting_profile', 'legacy_id',),
        }),
    )


@admin.register(NetworkServiceGroup)
class NetworkServiceGroupAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ("name",)}

    filter_horizontal = ('network_services',)

    fieldsets = (
        (None, {
            'fields': (
                'name', 'slug', 'description', 'network_services',),
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


class NetworkServiceL2AdminInline(admin.StackedInline):
    model = NetworkServiceL2
    extra = 0

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
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'network_service_device':
            kwargs['queryset'] = NetworkServiceDevice.objects.order_by('network_service__member__name')
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    fieldsets = (
        (None, {
            'fields': (
                'network_service_device',),
        }),

        ('Member / Service Provider', {
            'fields': (
                'member', 'member_site'),
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


class NetworkServiceL3AdminInline(admin.StackedInline):
    model = NetworkServiceL3
    extra = 0

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'network_service_device':
            kwargs['queryset'] = NetworkServiceDevice.objects.order_by('network_service__member__name')
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

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


class NetworkServiceDeviceAdminActiveFilter(admin.SimpleListFilter):
    title = 'Active'
    parameter_name = 'active'

    def lookups(self, request, model_admin):
        return (
            (True, 'Yes'),
            (False, 'No'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'True':
            return queryset.filter(network_service__active=True)
        if self.value() == 'False':
            return queryset.filter(network_service__active=False)
        if self.value() == 'all':
            return queryset
        if self.value() is None:
            return queryset.filter(network_service__active=True)


@admin.register(NetworkServiceDevice)
class NetworkServiceDeviceAdmin(admin.ModelAdmin):
    ordering = ['network_service']
    list_filter = (NetworkServiceDeviceAdminActiveFilter,)
    inlines = (NetworkServiceL3AdminInline, NetworkServiceL2AdminInline,)

    fieldsets = (
        (None, {
            'fields': ('network_service',),
        }),

        ('Configuration', {
            'fields': (
                'device', 'interface', 'vlan', 'comments'),
        }),

    )

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'network_service':
            kwargs['queryset'] = NetworkService.objects.filter(active=True).order_by('member__name')
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


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
                'out_rate', 'in_rate',
            ),
        }),
    )


@admin.register(RoutingType)
class RoutingTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
