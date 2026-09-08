"""
Builders for the netflow ClickHouse dimension rows.

These functions produce the fully-resolved row sets for the ``pmacct``
dimension tables on the netflow platform:

  - :func:`build_interface_label_rows`   -> ``dim_interface_labels``
  - :func:`build_accounting_source_rows` -> ``dim_accounting_sources``
  - :func:`build_member_rows`            -> ``dim_members`` +
    ``dim_member_prefixes``

The builders are shared between:

  - the ``export_data_to_clickhouse`` management command (the historical
    nightly push from the NetBox host), and
  - the ``clickhouse-dims`` API endpoint (read by the netflow-side pull
    script, ``pull_sidekick_dims.py``).

Keeping the row-building in one module guarantees both paths produce
identical rows. Rows intentionally do NOT include ``updated_at``; callers
stamp it at write time.

None of these functions talk to ClickHouse — they are pure Django/ORM data
builders and are safe to call from the API request path.
"""

from typing import Any, Dict, List, Tuple

from django.utils.text import slugify

from dcim.models import Interface

from sidekick.models import (
    AccountingProfile,
    AccountingSource,
    NetworkService,
    NetworkServiceDevice,
)


def graphite_device_name(device_name: str) -> str:
    return (
        device_name.lower()
        .replace(" ", "_")
        .replace(".", "_")
        .replace("(", "")
        .replace(")", "")
    )


def graphite_interface_name(interface_name: str) -> str:
    return (
        interface_name.lower()
        .replace("/", "-")
        .replace(".", "_")
        .replace("(", "")
        .replace(")", "")
    )


def build_service_map() -> Tuple[Dict[Tuple[int, str], NetworkServiceDevice], List[Tuple[int, str]]]:
    """Map (device_id, interface name) -> NetworkServiceDevice for active services.

    When multiple NetworkServiceDevice rows claim the same (device,
    interface) pair, the first instance wins and the key is reported as a
    duplicate.
    """
    service_map: Dict[Tuple[int, str], NetworkServiceDevice] = {}
    duplicates: List[Tuple[int, str]] = []

    nsd_qs = (
        NetworkServiceDevice.objects
        .select_related("network_service__member", "device")
        .filter(network_service__active=True)
    )

    for nsd in nsd_qs:
        if nsd.device_id is None or not nsd.interface:
            continue
        key = (nsd.device_id, nsd.interface)
        if key in service_map:
            duplicates.append(key)
            continue
        service_map[key] = nsd

    return service_map, duplicates


def build_interface_label_rows() -> Tuple[List[Dict[str, Any]], List[Tuple[int, str]]]:
    """Rows for pmacct.dim_interface_labels.

    Returns (rows, duplicate_service_mappings). One row per NetBox
    interface, annotated with the device's graphite segments and — when the
    interface belongs to an active NetworkServiceDevice — the service and
    member it belongs to.
    """
    service_map, duplicates = build_service_map()

    rows: List[Dict[str, Any]] = []

    qs = Interface.objects.select_related("device")

    for iface in qs.iterator(chunk_size=2000):
        device = iface.device
        if device is None:
            continue

        device_segment = graphite_device_name(device.name)
        interface_segment = graphite_interface_name(iface.name)
        graphite_base = f"{device_segment}.{interface_segment}"

        member_id = None
        member_name = None
        member_slug = None
        service_id = None
        service_name = None
        service_slug = None
        graphite_service_prefix = None

        nsd = service_map.get((device.id, iface.name))
        if nsd and nsd.network_service:
            ns = nsd.network_service
            service_id = ns.id
            service_name = ns.name
            service_slug = slugify(ns.name)
            if ns.member:
                member_id = ns.member.id
                member_name = ns.member.name
                member_slug = slugify(ns.member.name)
            graphite_service_prefix = f"{ns.graphite_service_name()}.{graphite_base}"

        rows.append(
            {
                "interface_id": iface.id,
                "device_id": device.id,
                "device_name": device.name,
                "interface_name": iface.name,
                "device_segment": device_segment,
                "interface_segment": interface_segment,
                "graphite_base": graphite_base,
                "member_id": member_id,
                "member_name": member_name,
                "member_slug": member_slug,
                "service_id": service_id,
                "service_name": service_name,
                "service_slug": service_slug,
                "graphite_service_prefix": graphite_service_prefix,
            }
        )

    return rows, duplicates


def build_accounting_source_rows() -> Tuple[List[Dict[str, Any]], int]:
    """Rows for pmacct.dim_accounting_sources.

    Returns (rows, backfilled_source_count).

    An AccountingProfile links a Tenant (member) to one or more
    AccountingSources. However, the same SCU/DCU class (identified by
    AccountingSource.name) can exist on multiple devices (e.g., an old
    MX480 and a new core router). Typically only the source on the newer
    device is linked to an AccountingProfile, leaving the old-device
    source's member_name NULL. To fix this, after building the direct
    mapping we backfill from siblings: any unlinked source whose name
    matches a linked source inherits that source's member info.
    """
    acc_member_map: Dict[int, Dict[str, str]] = {}
    for profile in AccountingProfile.objects.select_related('member').prefetch_related('accounting_sources'):
        if profile.member:
            for src in profile.accounting_sources.all():
                acc_member_map[src.id] = {
                    'name': profile.member.name,
                    'slug': slugify(profile.member.name)
                }

    backfilled = 0
    if acc_member_map:
        name_to_member: Dict[str, Dict[str, str]] = {}
        for src in AccountingSource.objects.filter(id__in=list(acc_member_map.keys())):
            name_to_member[src.name] = acc_member_map[src.id]

        for src in AccountingSource.objects.exclude(id__in=list(acc_member_map.keys())):
            if src.name in name_to_member:
                acc_member_map[src.id] = name_to_member[src.name]
                backfilled += 1

    rows: List[Dict[str, Any]] = []
    for acc in AccountingSource.objects.select_related("device"):
        graphite_prefix = "accounting.{}.{}".format(
            acc.graphite_name(),
            acc.graphite_destination_name())

        member_info = acc_member_map.get(acc.id, {})

        rows.append({
            "accounting_source_id": acc.id,
            "device_id": acc.device.id,
            "device_name": acc.device.name,
            "source_name": acc.name,
            "destination_name": acc.destination,
            "graphite_prefix": graphite_prefix,
            "member_name": member_info.get('name'),
            "member_slug": member_info.get('slug'),
        })

    return rows, backfilled


def build_member_rows() -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Rows for pmacct.dim_members and pmacct.dim_member_prefixes.

    Returns (member_rows, member_prefix_rows). Built from active
    transit/c-all network services. This mirrors the /fastnetmon_data/
    API endpoint's logic but uses Django slugify() for consistent slugs
    across all dim_* tables.
    """
    members_map: Dict[str, Dict[str, Any]] = {}

    services = NetworkService.objects.filter(
        active=True,
        network_service_type__name__in=['transit', 'c-all'],
    ).select_related('member', 'accounting_profile')

    for ns in services:
        if ns.member is None:
            continue

        member_name = ns.member.name
        member_slug = slugify(member_name)

        if member_slug not in members_map:
            traffic_cap = None
            if ns.accounting_profile is not None:
                bp = ns.accounting_profile.get_current_bandwidth_profile()
                if bp is not None and bp.traffic_cap is not None:
                    traffic_cap = bp.traffic_cap

            members_map[member_slug] = {
                'member_id': ns.member.id,
                'member_name': member_name,
                'member_slug': member_slug,
                'traffic_cap_mbps': traffic_cap,
                'prefixes': set(),
            }

        for prefix in ns.get_prefixes(version=4):
            members_map[member_slug]['prefixes'].add(str(prefix))

        for prefix in ns.get_prefixes(version=6):
            members_map[member_slug]['prefixes'].add(str(prefix))

    member_rows: List[Dict[str, Any]] = []
    member_prefix_rows: List[Dict[str, Any]] = []
    for slug, data in sorted(members_map.items()):
        member_rows.append({
            'member_id': data['member_id'],
            'member_name': data['member_name'],
            'member_slug': slug,
            'traffic_cap_mbps': data['traffic_cap_mbps'],
        })
        for prefix in sorted(data['prefixes']):
            member_prefix_rows.append({
                'prefix': prefix,
                'member_slug': slug,
            })

    return member_rows, member_prefix_rows
