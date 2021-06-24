import django_tables2 as tables

from utilities.tables import BaseTable, ToggleColumn

from sidekick.models import (
    AccountingProfile,
    AccountingClass,
    BandwidthProfile,
)


NAME_LINK = """
    <a href="{{ record.get_absolute_url }}">{{ record }}</a>
"""

MEMBER_LINK = """
    <a href="{{ record.accounting_profile.member.get_absolute_url }}">
        {{ record.accounting_profile.member.name }}
    </a>
"""


class AccountingProfileTable(BaseTable):
    pk = ToggleColumn()
    name = tables.TemplateColumn(
        template_code=NAME_LINK,
        verbose_name='Profile Name',
    )

    traffic_cap = tables.Column(empty_values=())
    burst_limit = tables.Column(empty_values=())

    def render_traffic_cap(self, value, record):
        return record.get_current_bandwidth_profile().traffic_cap

    def render_burst_limit(self, value, record):
        return record.get_current_bandwidth_profile().burst_limit

    class Meta(BaseTable.Meta):
        model = AccountingProfile
        fields = (
            'pk', 'name', 'enabled',
        )


class AccountingClassTable(BaseTable):
    pk = ToggleColumn()
    name = tables.LinkColumn()

    class Meta(BaseTable.Meta):
        model = AccountingClass
        fields = ('pk', 'device', 'name', 'destination')


class BandwidthProfileTable(BaseTable):
    pk = ToggleColumn()
    member = tables.TemplateColumn(
        template_code=MEMBER_LINK,
        verbose_name='Member',
    )

    class Meta(BaseTable.Meta):
        model = BandwidthProfile
        fields = ('pk', 'member', 'traffic_cap', 'burst_limit')
