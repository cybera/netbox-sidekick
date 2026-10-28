from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from netbox.api.authentication import TokenAuthentication
from netbox.api.viewsets import NetBoxModelViewSet

from sidekick.api.serializers import MemberTenantSerializer
from sidekick.filtersets import MemberTenantFilterSet
from sidekick.models import MemberTenant
from sidekick.utils.membership import resolve_entitlement


class MemberTenantViewSet(NetBoxModelViewSet):
    queryset = MemberTenant.objects.select_related('user', 'tenant')
    serializer_class = MemberTenantSerializer
    filterset_class = MemberTenantFilterSet


class EntitlementView(APIView):
    """
    What one address may act for: the members, the role held on each, and why.

    This is the single answer the portal, the MCP front door and any report use, so
    that granting access in one place grants it everywhere. `?address=` is the
    account's sign-in address and is matched case-insensitively.

    Read-only, and it fails closed: an unknown address, an inactive account or an
    account holding no entitlement all return an empty `tenants` list with a `reason`
    naming which of those it was. A caller must treat anything other than
    `reason = entitled` as no access, never as a default.

    `found` is true only when the account exists and is active, which lets a caller
    tell "we do not know this person" from "this person has no members yet".
    """

    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]

    def get(self, request):
        address = (request.query_params.get('address') or '').strip()
        resolved = resolve_entitlement(address)
        user = resolved['user']
        return Response({
            'address': address,
            'found': user is not None and user.is_active,
            'account': user.username if user is not None else None,
            'reason': resolved['reason'],
            'tenants': [
                {
                    'id': tenant.pk,
                    'name': tenant.name,
                    'slug': tenant.slug,
                    'role': resolved['roles'].get(tenant.pk),
                }
                for tenant in resolved['tenants']
            ],
        })
