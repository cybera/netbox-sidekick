import django_tables2 as tables

from netbox.tables import BaseTable, ChoiceFieldColumn, ToggleColumn
from users.tables import UserTable

from sidekick.models import MemberTenant

ACCOUNT_LINK = """
    <a href="{{ record.user.get_absolute_url }}">{{ record.user }}</a>
"""

MEMBER_LINK = """
    <a href="{{ record.tenant.get_absolute_url }}">{{ record.tenant.name }}</a>
"""


class MemberTenantTable(BaseTable):
    pk = ToggleColumn()
    user = tables.TemplateColumn(template_code=ACCOUNT_LINK, verbose_name='Account', orderable=False)
    tenant = tables.TemplateColumn(template_code=MEMBER_LINK, verbose_name='Member', orderable=False)
    role = ChoiceFieldColumn()
    note = tables.Column(verbose_name='Note')

    class Meta(BaseTable.Meta):
        model = MemberTenant
        fields = ('pk', 'user', 'tenant', 'role', 'note')
        default_columns = ('user', 'tenant', 'role', 'note')


class MemberTenantForUserTable(BaseTable):
    """The entitlements of one account, for the account page."""

    tenant = tables.TemplateColumn(template_code=MEMBER_LINK, verbose_name='Member', orderable=False)
    role = ChoiceFieldColumn()

    class Meta(BaseTable.Meta):
        model = MemberTenant
        fields = ('tenant', 'role', 'note')
        default_columns = ('tenant', 'role', 'note')
        attrs = {'class': 'table table-hover'}


__all__ = ('MemberTenantTable', 'MemberTenantForUserTable', 'UserTable')
