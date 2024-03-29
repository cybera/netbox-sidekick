import django_tables2 as tables

from netbox.tables import BaseTable, ToggleColumn

from sidekick.models import LogicalSystem


LINK = """
    <a href="/plugins/sidekick/member_bandwidth/{{ record.id }}">{{ record }}</a>
"""


class MemberBandwidthTable(BaseTable):
    pk = ToggleColumn()
    member = tables.TemplateColumn(
        template_code=LINK,
        verbose_name='Member',
    )

    class Meta(BaseTable.Meta):
        model = LogicalSystem
        fields = ('pk', 'member',)


class MemberContactTable(tables.Table):
    contact = tables.Column()
