import django_tables2 as tables

from django.db.models import Count
from django_tables2.utils import Accessor

from utilities.tables import BaseTable, ToggleColumn

from netbox_sidekick.models import MemberNodeType, MemberNode

OWNER_LINK = """
    <a href="{{ record.owner.get_absolute_url }}">{{ record.owner.tenant.description }}</a>
"""


class MemberNodeTypeTable(BaseTable):
    pk = ToggleColumn()
    name = tables.LinkColumn()

    # Create a column that shows how many nodes
    # are associated with each type.
    nodes = tables.Column(
        accessor=Accessor('member_node_count'))

    class Meta(BaseTable.Meta):
        model = MemberNodeType
        order_by = ('name',)
        fields = ('pk', 'name', 'nodes')

    # Because "nodes" is a virtual/computed column,
    # we need to implement sorting logic here.
    def order_nodes(self, queryset, is_descending):
        queryset = queryset.annotate(
            v=Count("membernode__id")
        ).order_by(("-" if is_descending else "") + "v")
        return (queryset, True)


class MemberNodeTable(BaseTable):
    pk = ToggleColumn()
    name = tables.LinkColumn()

    owner = tables.TemplateColumn(
        template_code=OWNER_LINK,
        verbose_name='Owner',
    )
    node_type = tables.LinkColumn()

    class Meta(BaseTable.Meta):
        model = MemberNode
        order_by = ('name',)
        fields = ('pk', 'name', 'label', 'node_type', 'owner')
