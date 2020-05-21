import django_tables2 as tables

from django.db.models import Count
from django_tables2.utils import Accessor

from utilities.tables import BaseTable, ToggleColumn

from netbox_sidekick.models import MemberType, Member


MEMBER_LINK = """
    <a href="{{ record.get_absolute_url }}">{{ record }}</a>
"""


class MemberTypeTable(BaseTable):
    pk = ToggleColumn()
    name = tables.LinkColumn()

    # Create a column that shows how many members
    # are associated with each type.
    members = tables.Column(
        accessor=Accessor('member_count'))

    class Meta(BaseTable.Meta):
        model = MemberType
        order_by = ('name',)
        fields = ('pk', 'name', 'members')

    # Because "members" is a virtual/computed column,
    # we need to implement sorting logic here.
    def order_members(self, queryset, is_descending):
        queryset = queryset.annotate(
            v=Count("member__id")
        ).order_by(("-" if is_descending else "") + "v")
        return (queryset, True)


class MemberTable(BaseTable):
    pk = ToggleColumn()
    tenant = tables.TemplateColumn(
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
        order_by = ('tenant',)
        fields = (
            'pk', 'tenant', 'member_type', 'active',
            'start_date', 'number_of_users',)
