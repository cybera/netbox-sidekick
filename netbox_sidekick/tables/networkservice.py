import django_tables2 as tables

from django_tables2.utils import Accessor

from utilities.tables import BaseTable, ToggleColumn

from netbox_sidekick.models import (
    LogicalSystem, RoutingType,
    NetworkServiceConnectionType, NetworkServiceConnection,
)

TENANT_LINK = """
    <a href="{{ record.tenant.get_absolute_url }}">{{ record.tenant.description }}</a>
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


class NetworkServiceConnectionTypeTable(BaseTable):
    pk = ToggleColumn()
    name = tables.LinkColumn()

    class Meta(BaseTable.Meta):
        model = NetworkServiceConnectionType
        fields = ('pk', 'name', 'description')


class NetworkServiceConnectionTable(BaseTable):
    pk = ToggleColumn()

    name = tables.LinkColumn(
        'plugins:netbox_sidekick:networkserviceconnection_detail',
        args=[Accessor('pk')])

    network_service_type = tables.LinkColumn(
        'plugins:netbox_sidekick:networkservicetypeconnection_detail',
        args=[Accessor('network_service_connection_type.slug')])

    member = tables.TemplateColumn(
        template_code=TENANT_LINK,
        verbose_name='Member',
    )

    class Meta(BaseTable.Meta):
        model = NetworkServiceConnection
        fields = ('pk', 'name', 'network_service_connection_type', 'tenant')
