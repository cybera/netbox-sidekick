import django_tables2 as tables

from netbox.tables import BaseTable, ToggleColumn

from sidekick.models import TransitRate

MEMBER_LINK = """
    <a href="{{ record.tenant.get_absolute_url }}">{{ record.tenant.name }}</a>
"""


class TransitRateTable(BaseTable):
    pk = ToggleColumn()
    tenant = tables.TemplateColumn(
        template_code=MEMBER_LINK,
        verbose_name='Member',
        orderable=False,
    )
    scope = tables.Column(
        accessor='is_global',
        verbose_name='Scope',
        orderable=False,
    )

    def render_scope(self, value):
        return 'Global default' if value else 'Member override'

    class Meta(BaseTable.Meta):
        model = TransitRate
        fields = ('pk', 'tenant', 'scope', 'rate_per_mbit', 'effective_date')
        default_columns = ('pk', 'tenant', 'scope', 'rate_per_mbit', 'effective_date')
