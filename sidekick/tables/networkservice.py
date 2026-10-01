import django_tables2 as tables

from django_tables2.utils import Accessor

from netbox.tables import BaseTable, ToggleColumn

from sidekick.models import (
    LogicalSystem, RoutingType,
    NetworkServiceType, NetworkService, NetworkServiceL3,
    NetworkServiceDevice, NetworkServiceL2,
    NetworkServiceGroup,
)

NETWORK_SERVICE_LINK = """
    <a href="{{ record.get_absolute_url }}">{{ record }}</a>
"""

TENANT_LINK = """
    <a href="{{ record.member.get_absolute_url }}">{{ record.member.name }}</a>
"""

PEERING_LINK = """
    <a href="{{ record.get_absolute_url }}">{{ record }}</a>
"""


class LogicalSystemTable(BaseTable):
    pk = ToggleColumn()
    name = tables.LinkColumn()

    class Meta(BaseTable.Meta):
        model = LogicalSystem
        fields = ('pk', 'name', 'slug')


class RoutingTypeTable(BaseTable):
    pk = ToggleColumn()
    name = tables.LinkColumn()

    class Meta(BaseTable.Meta):
        model = RoutingType
        fields = ('pk', 'name', 'slug')


class NetworkServiceTypeTable(BaseTable):
    pk = ToggleColumn()
    name = tables.LinkColumn()

    class Meta(BaseTable.Meta):
        model = NetworkServiceType
        fields = ('pk', 'name', 'description')


class NetworkServiceTable(BaseTable):
    pk = ToggleColumn()

    name = tables.TemplateColumn(
        template_code=NETWORK_SERVICE_LINK,
        verbose_name='Network Service',
    )

    network_service_type = tables.LinkColumn(
        'plugins:sidekick:networkservicetype',
        args=[Accessor('network_service_type.pk')])

    member = tables.TemplateColumn(
        template_code=TENANT_LINK,
        verbose_name='Member',
    )

    class Meta(BaseTable.Meta):
        model = NetworkService
        fields = ('pk', 'active', 'id', 'legacy_id', 'name', 'network_service_type', 'member', 'member_site')

    def order_name(self, queryset, is_descending):
        member_field = 'member__name'
        service_field = 'name'
        if is_descending:
            member_field = '-member_name'
            service_field = '-name'
        queryset = queryset.order_by(member_field, service_field)
        return (queryset, True)


class NetworkServiceGroupTable(BaseTable):
    pk = ToggleColumn()
    name = tables.LinkColumn()

    class Meta(BaseTable.Meta):
        model = NetworkServiceGroup
        fields = ('pk', 'name', 'description')


class NetworkServiceL3Table(BaseTable):
    pk = ToggleColumn()

    name = tables.TemplateColumn(
        template_code=NETWORK_SERVICE_LINK,
    )

    member = tables.TemplateColumn(
        template_code=TENANT_LINK,
        verbose_name='Member',
    )

    class Meta(BaseTable.Meta):
        model = NetworkServiceL3
        fields = ('pk', 'active', 'id', 'name', 'network_service_device',)

    def order_name(self, queryset, is_descending):
        member_field = 'member__name'
        service_field = 'name'
        if is_descending:
            member_field = '-member_name'
            service_field = '-name'
        queryset = queryset.order_by(member_field, service_field)
        return (queryset, True)


class PeeringConnectionTable(BaseTable):
    pk = ToggleColumn()

    name = tables.TemplateColumn(
        template_code=PEERING_LINK,
        verbose_name='Peering Connection',
    )

    member = tables.TemplateColumn(
        template_code=TENANT_LINK,
        verbose_name='Member',
    )

    class Meta(BaseTable.Meta):
        model = NetworkServiceL3
        fields = ('pk', 'active', 'id', 'name', 'member', 'member_site')

    def order_name(self, queryset, is_descending):
        member_field = 'member__name'
        service_field = 'name'
        if is_descending:
            member_field = '-member_name'
            service_field = '-name'
        queryset = queryset.order_by(member_field, service_field)
        return (queryset, True)


class NetworkServiceDeviceTable(BaseTable):
    pk = ToggleColumn()

    network_service = tables.LinkColumn(
        'plugins:sidekick:networkservice',
        args=[Accessor('network_service.pk')],
    )

    device = tables.LinkColumn(
        'dcim:device',
        args=[Accessor('device.pk')],
    )

    class Meta(BaseTable.Meta):
        model = NetworkServiceDevice
        fields = ('pk', 'network_service', 'device', 'interface', 'vlan')


class NetworkServiceL2Table(BaseTable):
    pk = ToggleColumn()

    network_service_device = tables.LinkColumn(
        'plugins:sidekick:networkservicedevice',
        args=[Accessor('network_service_device.pk')],
    )

    class Meta(BaseTable.Meta):
        model = NetworkServiceL2
        fields = ('pk', 'network_service_device', 'vlan')
