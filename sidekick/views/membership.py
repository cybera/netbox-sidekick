from netbox.object_actions import AddObject, BulkDelete, BulkExport, BulkImport
from netbox.views import generic
from utilities.views import register_model_view

from sidekick import filtersets, forms, tables
from sidekick.models import MemberTenant

from .base import SidekickObjectView


@register_model_view(MemberTenant, 'list', path='', detail=False)
class MemberTenantListView(generic.ObjectListView):
    queryset = MemberTenant.objects.select_related('user', 'tenant')
    table = tables.MemberTenantTable
    filterset = filtersets.MemberTenantFilterSet
    filterset_form = filtersets.MemberTenantFilterSetForm
    actions = (AddObject, BulkImport, BulkExport, BulkDelete)


@register_model_view(MemberTenant)
class MemberTenantView(SidekickObjectView):
    queryset = MemberTenant.objects.select_related('user', 'tenant')


@register_model_view(MemberTenant, 'add', detail=False)
@register_model_view(MemberTenant, 'edit')
class MemberTenantEditView(generic.ObjectEditView):
    queryset = MemberTenant.objects.all()
    form = forms.MemberTenantForm


@register_model_view(MemberTenant, 'delete')
class MemberTenantDeleteView(generic.ObjectDeleteView):
    queryset = MemberTenant.objects.all()


@register_model_view(MemberTenant, 'bulk_import', path='import', detail=False)
class MemberTenantBulkImportView(generic.BulkImportView):
    queryset = MemberTenant.objects.all()
    model_form = forms.MemberTenantImportForm
