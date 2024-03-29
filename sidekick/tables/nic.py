import django_tables2 as tables

from netbox.tables import BaseTable, ToggleColumn

from sidekick.models import (
    NIC,
)

DEVICE_LINK = """
    <a href="{{ record.interface.device.get_absolute_url }}">{{ record.interface.device.name }}</a>
"""

NIC_LINK = """
    <a href="{{ record.get_absolute_url }}">{{ record.interface.name }}</a>
"""

DESCRIPTION = "{{ record.interface.description }}"


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

    description = tables.TemplateColumn(
        template_code=DESCRIPTION,
        verbose_name='Description',
    )

    class Meta(BaseTable.Meta):
        model = NIC
        fields = ('pk', 'interface', 'device', 'description',)

    def order_interface(self, queryset, is_descending):
        field = 'interface__name'
        if is_descending:
            field = '-interface__name'
        queryset = queryset.order_by(field, 'interface__id').distinct('interface__name', 'interface__id')
        return (queryset, True)
