from netbox.views import generic
from utilities.views import GetRelatedModelsMixin


class SidekickObjectView(GetRelatedModelsMixin, generic.ObjectView):
    """
    Base object detail view for sidekick models.

    Renders a panel layout (``generic/object.html``) and annotates related
    objects for the ``RelatedObjectsPanel``.
    """
    template_name = 'generic/object.html'
