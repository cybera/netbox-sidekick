from netbox.plugins import PluginTemplateExtension

from sidekick.models import MemberTenant


class TenantEntitlementsPanel(PluginTemplateExtension):
    """List the accounts entitled to a member on the member's own page.

    The row is the record, so it belongs where the member is managed rather than in
    Admin -> Users. Every action (add, edit, delete) links into the sidekick views, so
    nothing about entitlement needs the Django admin or a shell.

    Rendered for every tenant, but only when there is something to show or the tenant
    is a member: an empty card on every tenant page would be noise.
    """

    models = ['tenancy.tenant']

    def full_width_page(self):
        tenant = self.context['object']
        grants = (
            MemberTenant.objects.filter(tenant=tenant)
            .select_related('user')
            .order_by('user__username')
        )
        if not grants and getattr(tenant.group, 'name', None) != 'Members':
            return ''
        return self.render(
            'sidekick/template_content/tenant_entitlements.html',
            extra_context={'grants': grants, 'tenant': tenant},
        )
