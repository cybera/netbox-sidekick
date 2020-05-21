from rest_framework.viewsets import ModelViewSet
from netbox_sidekick.models import Member
from netbox_sidekick.api.serializers import MemberSerializer


class MemberViewSet(ModelViewSet):
    queryset = Member.objects.all()
    serializer_class = MemberSerializer
