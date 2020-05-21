from django.contrib import admin

from .models import (
    ContactType, Contact,
    MemberType, Member, MemberContact,
    MemberNodeType, MemberNode,
    MemberNodeLinkType, MemberNodeLink,
    NetworkServiceType, NetworkService
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


@admin.register(MemberType)
class MemberTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')


@admin.register(Member)
class MemberAdmin(admin.ModelAdmin):
    fieldsets = (
        ('Member', {
            'fields': ('tenant', 'user', 'member_type'),
        }),

        ('General', {
            'fields': (
                'start_date', 'invoice_period_start', 'active',
                'billing_exempt', 'number_of_users',),
        }),

        ('Billing', {
            'fields': (
                'billing_address_1', 'billing_address_2', 'billing_city',
                'billing_postal_code', 'billing_province', 'billing_country',),
        }),

        ('Miscellaneous', {
            'fields': ('supernet', 'latitude', 'longitude', 'url',),
        })
    )


@admin.register(MemberContact)
class MemberContactAdmin(admin.ModelAdmin):
    list_display = (
        'member', 'contact', 'type'
    )


@admin.register(MemberNodeType)
class MemberNodeTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')


@admin.register(MemberNode)
class MemberNodeAdmin(admin.ModelAdmin):
    list_display = (
        'owner', 'name', 'label', 'internal_id', 'node_type',
        'latitude', 'longitude', 'altitude', 'address',)


@admin.register(MemberNodeLinkType)
class MemberNodeLinkTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')


@admin.register(MemberNodeLink)
class MemberNodeLinkAdmin(admin.ModelAdmin):
    list_display = (
        'owner', 'name', 'label', 'internal_id', 'link_type',
        'a_endpoint', 'z_endpoint', 'throughput',)


@admin.register(NetworkServiceType)
class NetworkServiceTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')


@admin.register(NetworkService)
class NetworkServiceAdmin(admin.ModelAdmin):
    list_display = ('member', 'network_service_type', 'asn', 'comments')
