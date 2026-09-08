from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework.views import APIView

from sidekick.utils.clickhouse import now_utc_str
from sidekick.utils.dims import (
    build_accounting_source_rows,
    build_interface_label_rows,
    build_member_rows,
)

DIM_TABLES = ('interface_labels', 'accounting_sources', 'members', 'member_prefixes')


class ClickHouseDimsView(APIView):
    """Returns fully-resolved rows for the netflow ClickHouse dim_* tables.

    This endpoint is read by the netflow-side pull script
    (``pull_sidekick_dims.py``, cron on netflow.cybera.ca) to refresh
    ``pmacct.dim_interface_labels``, ``dim_accounting_sources``,
    ``dim_members`` and ``dim_member_prefixes``. Row-building is shared with
    the ``export_data_to_clickhouse`` management command via
    ``sidekick.utils.dims``, guaranteeing the push and pull produce
    identical rows.

    Query params:
        tables: repeatable subset of
            ['interface_labels', 'accounting_sources', 'members',
             'member_prefixes'] (default: all four)

    Response shape::

        {
          "generated_at": "2026-09-08 03:20:01",
          "interface_labels": [ {...}, ... ],
          "accounting_sources": [ {...}, ... ],
          "members": [ {...}, ... ],
          "member_prefixes": [ {...}, ... ]
        }

    Rows do not include ``updated_at``; the pull script stamps it at
    insert time.
    """
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    renderer_classes = (JSONRenderer,)

    def get(self, request):
        tables = request.query_params.getlist('tables', list(DIM_TABLES))
        unknown = [t for t in tables if t not in DIM_TABLES]
        if unknown:
            return Response(
                {"error": f"unknown tables: {unknown}; valid: {list(DIM_TABLES)}"},
                status=400,
            )

        payload = {"generated_at": now_utc_str()}

        if 'interface_labels' in tables:
            rows, duplicates = build_interface_label_rows()
            payload['interface_labels'] = rows
            payload['interface_labels_duplicate_mappings'] = len(duplicates)

        if 'accounting_sources' in tables:
            rows, backfilled = build_accounting_source_rows()
            payload['accounting_sources'] = rows
            payload['accounting_sources_backfilled'] = backfilled

        if 'members' in tables or 'member_prefixes' in tables:
            member_rows, prefix_rows = build_member_rows()
            if 'members' in tables:
                payload['members'] = member_rows
            if 'member_prefixes' in tables:
                payload['member_prefixes'] = prefix_rows

        return Response(payload)
