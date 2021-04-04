import django_tables2 as tables

from utilities.tables import BaseTable, ToggleColumn

from netbox_sidekick.models import (
    NIC,
)

DEVICE_LINK = """
    <a href="{{ record.interface.device.get_absolute_url }}">{{ record.interface.device.name }}</a>
"""

NIC_LINK = """
    <a href="{{ record.get_absolute_url }}">{{ record.interface.name }}</a>
"""


class NICTable(BaseTable):
    pk = ToggleColumn()
    interface = tables.TemplateColumn(
        template_code=NIC_LINK,
        verbose_name='Interface',
    )

    device = tables.TemplateColumn(
        template_code=DEVICE_LINK,
        verbose_name='Device',
    )

    class Meta(BaseTable.Meta):
        model = NIC
        fields = ('pk',)

    def order_interface(self, queryset, is_descending):
        field = 'interface__name'
        if is_descending:
            field = '-interface__name'
        queryset = queryset.order_by(field, 'interface__id').distinct('interface__name', 'interface__id')
        return (queryset, True)
