import django_tables2 as tables

from django_tables2.utils import Accessor

from tenancy.tables import COL_TENANT
from utilities.tables import BaseTable, ToggleColumn

from netbox_sidekick.models import NetworkServiceType, NetworkService


class NetworkServiceTypeTable(BaseTable):
    pk = ToggleColumn()
    name = tables.LinkColumn()

    class Meta(BaseTable.Meta):
        model = NetworkServiceType
        fields = ('pk', 'name', 'description')


class NetworkServiceTable(BaseTable):
    pk = ToggleColumn()

    name = tables.LinkColumn(
        'plugins:netbox_sidekick:networkservice_detail',
        args=[Accessor('pk')])

    network_service_type = tables.LinkColumn(
        'plugins:netbox_sidekick:networkservicetype_detail',
        args=[Accessor('network_service_type.slug')])

    tenant = tables.TemplateColumn(template_code=COL_TENANT)

    class Meta(BaseTable.Meta):
        model = NetworkService
        fields = ('pk', 'name', 'network_service_type', 'tenant')
