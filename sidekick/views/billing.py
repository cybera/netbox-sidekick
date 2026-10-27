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
