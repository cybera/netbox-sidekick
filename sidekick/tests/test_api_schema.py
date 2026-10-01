"""Guard against API views that break NetBox's generated API schema.

NetBox 4.x builds ``/api/schema/`` with drf-spectacular. Its
``NetBoxAutoSchema.get_description()`` falls back to reading
``self.view.queryset`` for any view that has no docstring, and
``_generate_description()`` then does::

    model_name = self.view.queryset.model._meta.verbose_name

so a view with no docstring *and* no queryset raises ``AttributeError`` and
takes the whole schema endpoint down with it. drf-spectacular's own
"unable to guess serializer ... Ignoring view for now" message is only a
graceful warning; this later failure is the one that is fatal.

That is not merely a documentation problem. ``netbox.netbox.nb_inventory``
introspects ``/api/schema/`` to discover which query filters exist, so a broken
schema makes every NetBox dynamic inventory fail to parse, which in turn makes
any playbook using one match zero hosts.

Note that ``getattr(view, 'queryset')`` is not a sufficient test: DRF's
generic views define ``queryset = None``, so a ``ListAPIView`` that builds its
queryset in ``get_queryset()`` still breaks the schema while appearing to have
a queryset attribute.
"""

from django.test import SimpleTestCase
from rest_framework.views import APIView

from sidekick.api import views


class APISchemaTest(SimpleTestCase):
    def test_api_views_are_schema_safe(self):
        offenders = []

        for name in dir(views):
            obj = getattr(views, name)
            if not isinstance(obj, type) or not issubclass(obj, APIView):
                continue
            if not obj.__module__.startswith('sidekick.'):
                continue
            if getattr(obj, 'queryset', None) is None and not obj.__doc__:
                offenders.append('%s.%s' % (obj.__module__, obj.__name__))

        self.assertEqual(
            sorted(set(offenders)), [],
            msg=(
                'These API views have neither a docstring nor a queryset. '
                'NetBox 4.x builds /api/schema/ with drf-spectacular, whose '
                'NetBoxAutoSchema.get_description() reads self.view.queryset '
                'for any view without a docstring, so a single one of these '
                'breaks the entire schema endpoint - and therefore every '
                'NetBox dynamic inventory. Add a docstring to each.'
            ),
        )
