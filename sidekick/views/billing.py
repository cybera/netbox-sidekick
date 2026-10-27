from netbox.object_actions import AddObject, BulkDelete, BulkExport, BulkImport
from netbox.views import generic
from utilities.views import register_model_view

from sidekick import filtersets, forms, tables
from sidekick.models import TransitRate

from .base import SidekickObjectView


@register_model_view(TransitRate, 'list', path='', detail=False)
class TransitRateListView(generic.ObjectListView):
    queryset = TransitRate.objects.all()
    table = tables.TransitRateTable
    filterset = filtersets.TransitRateFilterSet
    filterset_form = filtersets.TransitRateFilterSetForm
    # Bulk edit is left out of the default action set on purpose: it exists to set one
    # field across many rows, and on a rate row that would rewrite prices and dates that
    # a past bill is priced from. NetBox renders the button whether or not the bulk edit
    # view is registered (the button template does not check for a resolvable URL), so
    # the action is removed here as well as left unregistered below.
    actions = (AddObject, BulkImport, BulkExport, BulkDelete)


@register_model_view(TransitRate)
class TransitRateView(SidekickObjectView):
    queryset = TransitRate.objects.all()


@register_model_view(TransitRate, 'add', detail=False)
@register_model_view(TransitRate, 'edit')
class TransitRateEditView(generic.ObjectEditView):
    queryset = TransitRate.objects.all()
    form = forms.TransitRateForm


@register_model_view(TransitRate, 'delete')
class TransitRateDeleteView(generic.ObjectDeleteView):
    queryset = TransitRate.objects.all()


# No bulk edit on purpose: the view is not registered, and the action is also absent
# from TransitRateListView.actions because NetBox renders the button even when its URL
# does not resolve. Bulk rename is out for the same reason, and because the model has
# no name field.
@register_model_view(TransitRate, 'bulk_import', path='import', detail=False)
class TransitRateBulkImportView(generic.BulkImportView):
    queryset = TransitRate.objects.all()
    model_form = forms.TransitRateImportForm


@register_model_view(TransitRate, 'bulk_delete', path='delete', detail=False)
class TransitRateBulkDeleteView(generic.BulkDeleteView):
    queryset = TransitRate.objects.all()
    filterset = filtersets.TransitRateFilterSet
    table = tables.TransitRateTable
