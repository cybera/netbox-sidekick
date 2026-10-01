"""Panel and layout definitions for sidekick object detail views."""
from netbox.ui import attrs, layout, panels
from netbox.ui.panels import (
    CommentsPanel,
    ObjectsTablePanel,
    RelatedObjectsPanel,
)
from extras.ui.panels import CustomFieldsPanel, TagsPanel


#
# Panels
#

class LogicalSystemPanel(panels.ObjectAttributesPanel):
    name = attrs.TextAttr('name')
    slug = attrs.TextAttr('slug')


class RoutingTypePanel(panels.ObjectAttributesPanel):
    name = attrs.TextAttr('name')
    slug = attrs.TextAttr('slug')


class NetworkServiceTypePanel(panels.ObjectAttributesPanel):
    name = attrs.TextAttr('name')
    slug = attrs.TextAttr('slug')
    description = attrs.TextAttr('description')


class NetworkServicePanel(panels.ObjectAttributesPanel):
    name = attrs.TextAttr('name')
    network_service_type = attrs.RelatedObjectAttr('network_service_type', linkify=True)
    member = attrs.RelatedObjectAttr('member', linkify=True)
    member_site = attrs.RelatedObjectAttr('member_site', linkify=True)
    active = attrs.BooleanAttr('active')
    start_date = attrs.DateTimeAttr('start_date', spec='date')
    end_date = attrs.DateTimeAttr('end_date', spec='date')
    backup_for = attrs.RelatedObjectAttr('backup_for', linkify=True)
    accounting_profile = attrs.RelatedObjectAttr('accounting_profile', linkify=True)
    legacy_id = attrs.TextAttr('legacy_id')
    description = attrs.TextAttr('description')


class NetworkServiceDevicePanel(panels.ObjectAttributesPanel):
    network_service = attrs.RelatedObjectAttr('network_service', linkify=True)
    device = attrs.RelatedObjectAttr('device', linkify=True)
    interface = attrs.TextAttr('interface')
    vlan = attrs.NumericAttr('vlan')
    legacy_id = attrs.TextAttr('legacy_id')


class NetworkServiceL2Panel(panels.ObjectAttributesPanel):
    network_service_device = attrs.RelatedObjectAttr('network_service_device', linkify=True)
    vlan = attrs.NumericAttr('vlan')
    legacy_id = attrs.TextAttr('legacy_id')


class NetworkServiceL3Panel(panels.ObjectAttributesPanel):
    network_service_device = attrs.RelatedObjectAttr('network_service_device', linkify=True)
    member = attrs.RelatedObjectAttr('member', linkify=True)
    member_site = attrs.RelatedObjectAttr('member_site', linkify=True)
    logical_system = attrs.RelatedObjectAttr('logical_system', linkify=True)
    routing_type = attrs.RelatedObjectAttr('routing_type', linkify=True)
    asn = attrs.TextAttr('asn')
    active = attrs.BooleanAttr('active')
    ipv4_unicast = attrs.BooleanAttr('ipv4_unicast')
    ipv4_multicast = attrs.BooleanAttr('ipv4_multicast')
    ipv6_unicast = attrs.BooleanAttr('ipv6_unicast')
    ipv6_multicast = attrs.BooleanAttr('ipv6_multicast')
    provider_router_address_ipv4 = attrs.TextAttr('provider_router_address_ipv4')
    member_router_address_ipv4 = attrs.TextAttr('member_router_address_ipv4')
    provider_router_address_ipv6 = attrs.TextAttr('provider_router_address_ipv6')
    member_router_address_ipv6 = attrs.TextAttr('member_router_address_ipv6')
    legacy_id = attrs.TextAttr('legacy_id')


class NetworkServiceGroupPanel(panels.ObjectAttributesPanel):
    name = attrs.TextAttr('name')
    slug = attrs.TextAttr('slug')
    description = attrs.TextAttr('description')


class AccountingSourcePanel(panels.ObjectAttributesPanel):
    device = attrs.RelatedObjectAttr('device', linkify=True)
    name = attrs.TextAttr('name')
    destination = attrs.TextAttr('destination')


class AccountingProfilePanel(panels.ObjectAttributesPanel):
    member = attrs.RelatedObjectAttr('member', linkify=True)
    name = attrs.TextAttr('name')
    enabled = attrs.BooleanAttr('enabled')


class BandwidthProfilePanel(panels.ObjectAttributesPanel):
    accounting_profile = attrs.RelatedObjectAttr('accounting_profile', linkify=True)
    effective_date = attrs.DateTimeAttr('effective_date', spec='date')
    traffic_cap = attrs.NumericAttr('traffic_cap')
    burst_limit = attrs.NumericAttr('burst_limit')
    billable = attrs.BooleanAttr('billable')


class NICPanel(panels.ObjectAttributesPanel):
    interface = attrs.RelatedObjectAttr('interface', linkify=True)
    admin_status = attrs.NumericAttr('admin_status')
    oper_status = attrs.NumericAttr('oper_status')
    in_rate = attrs.NumericAttr('in_rate')
    out_rate = attrs.NumericAttr('out_rate')
    in_octets = attrs.NumericAttr('in_octets')
    out_octets = attrs.NumericAttr('out_octets')
    in_unicast_packets = attrs.NumericAttr('in_unicast_packets')
    out_unicast_packets = attrs.NumericAttr('out_unicast_packets')
    in_nunicast_packets = attrs.NumericAttr('in_nunicast_packets')
    out_nunicast_packets = attrs.NumericAttr('out_nunicast_packets')
    in_errors = attrs.NumericAttr('in_errors')
    out_errors = attrs.NumericAttr('out_errors')


#
# Layouts
#

LOGICAL_SYSTEM_LAYOUT = layout.SimpleLayout(
    left_panels=[LogicalSystemPanel(), TagsPanel(), CustomFieldsPanel()],
    right_panels=[RelatedObjectsPanel()],
    bottom_panels=[
        ObjectsTablePanel('sidekick.NetworkService', filters={'logical_system_id': lambda ctx: ctx['object'].pk}),
    ],
)

ROUTING_TYPE_LAYOUT = layout.SimpleLayout(
    left_panels=[RoutingTypePanel(), TagsPanel(), CustomFieldsPanel()],
    right_panels=[RelatedObjectsPanel()],
    bottom_panels=[
        ObjectsTablePanel('sidekick.NetworkService', filters={'routing_type_id': lambda ctx: ctx['object'].pk}),
    ],
)

NETWORK_SERVICE_TYPE_LAYOUT = layout.SimpleLayout(
    left_panels=[NetworkServiceTypePanel(), TagsPanel(), CustomFieldsPanel()],
    right_panels=[RelatedObjectsPanel()],
    bottom_panels=[
        ObjectsTablePanel('sidekick.NetworkService', filters={'network_service_type_id': lambda ctx: ctx['object'].pk}),
    ],
)

NETWORK_SERVICE_LAYOUT = layout.SimpleLayout(
    left_panels=[NetworkServicePanel(), CommentsPanel(), TagsPanel(), CustomFieldsPanel()],
    right_panels=[RelatedObjectsPanel()],
    bottom_panels=[
        ObjectsTablePanel('sidekick.NetworkServiceDevice', filters={'network_service_id': lambda ctx: ctx['object'].pk}),
    ],
)

NETWORK_SERVICE_DEVICE_LAYOUT = layout.SimpleLayout(
    left_panels=[NetworkServiceDevicePanel(), CommentsPanel(), TagsPanel(), CustomFieldsPanel()],
    right_panels=[RelatedObjectsPanel()],
    bottom_panels=[
        ObjectsTablePanel('sidekick.NetworkServiceL2', filters={'network_service_device_id': lambda ctx: ctx['object'].pk}),
        ObjectsTablePanel('sidekick.NetworkServiceL3', filters={'network_service_device_id': lambda ctx: ctx['object'].pk}),
    ],
)

NETWORK_SERVICE_L2_LAYOUT = layout.SimpleLayout(
    left_panels=[NetworkServiceL2Panel(), CommentsPanel(), TagsPanel(), CustomFieldsPanel()],
    right_panels=[RelatedObjectsPanel()],
)

NETWORK_SERVICE_L3_LAYOUT = layout.SimpleLayout(
    left_panels=[NetworkServiceL3Panel(), CommentsPanel(), TagsPanel(), CustomFieldsPanel()],
    right_panels=[RelatedObjectsPanel()],
)

NETWORK_SERVICE_GROUP_LAYOUT = layout.SimpleLayout(
    left_panels=[NetworkServiceGroupPanel(), TagsPanel(), CustomFieldsPanel()],
    right_panels=[RelatedObjectsPanel()],
    bottom_panels=[
        ObjectsTablePanel('sidekick.NetworkService', filters={'network_service_group_id': lambda ctx: ctx['object'].pk}),
    ],
)

ACCOUNTING_SOURCE_LAYOUT = layout.SimpleLayout(
    left_panels=[AccountingSourcePanel(), TagsPanel(), CustomFieldsPanel()],
    right_panels=[RelatedObjectsPanel()],
)

ACCOUNTING_PROFILE_LAYOUT = layout.SimpleLayout(
    left_panels=[AccountingProfilePanel(), CommentsPanel(), TagsPanel(), CustomFieldsPanel()],
    right_panels=[RelatedObjectsPanel()],
    bottom_panels=[
        ObjectsTablePanel('sidekick.BandwidthProfile', filters={'accounting_profile_id': lambda ctx: ctx['object'].pk}),
    ],
)

BANDWIDTH_PROFILE_LAYOUT = layout.SimpleLayout(
    left_panels=[BandwidthProfilePanel(), CommentsPanel(), TagsPanel(), CustomFieldsPanel()],
    right_panels=[RelatedObjectsPanel()],
)

NIC_LAYOUT = layout.SimpleLayout(
    left_panels=[NICPanel(), TagsPanel(), CustomFieldsPanel()],
    right_panels=[RelatedObjectsPanel()],
)
