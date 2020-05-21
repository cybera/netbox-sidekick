import django_tables2 as tables

from django.db.models import Count
from django_tables2.utils import Accessor

from utilities.tables import BaseTable, ToggleColumn

from netbox_sidekick.models import MemberNodeLinkType, MemberNodeLink


MEMBER_LINK = """
    <a href="{{ record.owner.get_absolute_url }}">{{ record.owner }}</a>
"""


class MemberNodeLinkTypeTable(BaseTable):
    pk = ToggleColumn()
    name = tables.LinkColumn()

    # Create a column that shows how many links
    # are associated with each type.
    links = tables.Column(
        accessor=Accessor('member_node_link_count'))

    class Meta(BaseTable.Meta):
        model = MemberNodeLinkType
        order_by = ('name',)
        fields = ('pk', 'name')

    # Because "members" is a virtual/computed column,
    # we need to implement sorting logic here.
    def order_links(self, queryset, is_descending):
        queryset = queryset.annotate(
            v=Count("membernodelink__id")
        ).order_by(("-" if is_descending else "") + "v")
        return (queryset, True)


class MemberNodeLinkTable(BaseTable):
    pk = ToggleColumn()
    name = tables.LinkColumn()

    owner = tables.TemplateColumn(
        template_code=MEMBER_LINK,
        verbose_name='Owner',
    )
    link_type = tables.LinkColumn()
    a_endpoint = tables.LinkColumn()
    z_endpoint = tables.LinkColumn()

    class Meta(BaseTable.Meta):
        model = MemberNodeLink
        order_by = ('name',)
        fields = (
            'pk', 'name', 'label', 'link_type', 'owner',
            'a_endpoint', 'z_endpoint', 'throughput')
