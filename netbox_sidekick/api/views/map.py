from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from netbox_sidekick.utils.gren_map import generate_map

from netbox_sidekick.api.renderers.plaintext import PlainTextRenderer


class FullMapViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]
    renderer_classes = (PlainTextRenderer,)

    def list(self, request):
        g = generate_map()
        return Response(g.write_to_string())
