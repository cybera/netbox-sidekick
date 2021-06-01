import django_tables2 as tables

from utilities.tables import BaseTable, ToggleColumn

from sidekick.models import ContactType, Contact


CONTACT_LINK = """
    <a href="{{ record.get_absolute_url }}">{{ record.last_name }}, {{ record.first_name }}</a>
"""


class ContactTypeTable(BaseTable):
    pk = ToggleColumn()
    name = tables.LinkColumn()

    class Meta(BaseTable.Meta):
        model = ContactType
        order_by = ('name',)
        fields = ('pk', 'name')


class ContactTable(BaseTable):
    pk = ToggleColumn()
    name = tables.TemplateColumn(
        template_code=CONTACT_LINK,
        verbose_name='Name',
        order_by=('last_name', 'first_name'),
    )

    class Meta(BaseTable.Meta):
        model = Contact
        order_by = ('last_name', 'first_name')
        fields = (
            'pk', 'name', 'title', 'email',
        )
