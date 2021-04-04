import django_tables2 as tables

from django_tables2.utils import Accessor

from utilities.tables import BaseTable, ToggleColumn

from netbox_sidekick.models import (
    LogicalSystem, RoutingType,
    NetworkServiceType, NetworkService,
)

NETWORK_SERVICE_LINK = """
    <a href="{{ record.get_absolute_url }}">{{ record }}</a>
"""

TENANT_LINK = """
    <a href="{{ record.member.get_absolute_url }}">{{ record.member.name }}</a>
"""


class LogicalSystemTable(BaseTable):
    pk = ToggleColumn()
    name = tables.LinkColumn()

    class Meta(BaseTable.Meta):
        model = LogicalSystem
        fields = ('pk', 'name', 'description')


class RoutingTypeTable(BaseTable):
    pk = ToggleColumn()
    name = tables.LinkColumn()

    class Meta(BaseTable.Meta):
        model = RoutingType
        fields = ('pk', 'name', 'description')


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
        'plugins:netbox_sidekick:networkservicetype_detail',
        args=[Accessor('network_service_type.slug')])

    member = tables.TemplateColumn(
        template_code=TENANT_LINK,
        verbose_name='Member',
    )

    class Meta(BaseTable.Meta):
        model = NetworkService
        fields = ('pk', 'active', 'id', 'name', 'network_service_type', 'member')

    def order_name(self, queryset, is_descending):
        member_field = 'member__name'
        service_field = 'name'
        if is_descending:
            member_field = '-member_name'
            service_field = '-name'
        queryset = queryset.order_by(member_field, service_field)
        return (queryset, True)
