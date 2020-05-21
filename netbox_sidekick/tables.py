import django_tables2 as tables
from django_tables2.utils import Accessor

from tenancy.tables import COL_TENANT
from utilities.tables import BaseTable, ToggleColumn

from .models import (
    MemberType, Member,
    MemberNodeType, MemberNode,
    MemberNodeLinkType, MemberNodeLink,
    NetworkServiceType, NetworkService,
)


MEMBER_LINK = """
    <a href="{{ record.get_absolute_url }}">{{ record }}</a>
"""


class MemberTypeTable(BaseTable):
    pk = ToggleColumn()
    name = tables.LinkColumn()

    class Meta(BaseTable.Meta):
        model = MemberType
        fields = ('pk', 'name')


class MemberTable(BaseTable):
    pk = ToggleColumn()
    member = tables.TemplateColumn(
        template_code=MEMBER_LINK,
        verbose_name='Member',
    )
    member_type = tables.LinkColumn()
    active = tables.BooleanColumn(
        verbose_name='Active',
    )
    start_date = tables.DateColumn(
        format="Y-m-d",
        verbose_name='Start Date',
    )

    class Meta(BaseTable.Meta):
        model = Member
        fields = (
            'pk', 'member', 'member_type', 'active',
            'start_date', 'number_of_users',)


class MemberNodeTypeTable(BaseTable):
    pk = ToggleColumn()
    name = tables.LinkColumn()

    class Meta(BaseTable.Meta):
        model = MemberNodeType
        fields = ('pk', 'name')


class MemberNodeTable(BaseTable):
    pk = ToggleColumn()
    name = tables.LinkColumn()

    owner = tables.TemplateColumn(
        template_code=MEMBER_LINK,
        verbose_name='Owner',
    )
    node_type = tables.LinkColumn()

    class Meta(BaseTable.Meta):
        model = MemberNode
        fields = ('pk', 'name', 'label', 'node_type', 'owner')


class MemberNodeLinkTypeTable(BaseTable):
    pk = ToggleColumn()
    name = tables.LinkColumn()

    class Meta(BaseTable.Meta):
        model = MemberNodeLinkType
        fields = ('pk', 'name')


class MemberNodeLinkTable(BaseTable):
    pk = ToggleColumn()
    name = tables.LinkColumn()

    owner = tables.TemplateColumn(
        template_code=MEMBER_LINK,
        verbose_name='Owner',
    )
    node_type = tables.LinkColumn()
    a_endpoint = tables.LinkColumn()
    z_endpoint = tables.LinkColumn()

    class Meta(BaseTable.Meta):
        model = MemberNodeLink
        fields = (
            'pk', 'name', 'label', 'node_type', 'owner',
            'a_endpoint', 'z_endpoint', 'throughput')


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
