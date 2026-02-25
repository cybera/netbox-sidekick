#!/usr/bin/env python3

import os
from typing import Any, Dict, List, Tuple

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils.text import slugify

from dcim.models import Interface

from sidekick.models import NetworkServiceDevice
from sidekick.utils.clickhouse import ClickHouseHTTP, now_utc_str


def sql_str(v: str) -> str:
    return "'" + v.replace("'", "''") + "'"


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


def table_exists(ch: ClickHouseHTTP, full_name: str) -> bool:
    if "." not in full_name:
        raise ValueError(f"Expected db.table, got: {full_name}")
    db, tbl = full_name.split(".", 1)
    q = (
        "SELECT toUInt8(count() > 0) "
        "FROM system.tables "
        f"WHERE database={sql_str(db)} AND name={sql_str(tbl)}"
    )
    return ch.execute_scalar_u8(q) == 1


def ensure_table(ch: ClickHouseHTTP, full_name: str) -> None:
    ch.execute(
        f"""
        CREATE TABLE IF NOT EXISTS {full_name}
        (
          interface_id UInt32,
          device_id UInt32,
          device_name String,
          interface_name String,
          device_segment String,
          interface_segment String,
          graphite_base String,
          member_id Nullable(UInt32),
          member_name Nullable(String),
          member_slug Nullable(String),
          service_id Nullable(UInt32),
          service_name Nullable(String),
          service_slug Nullable(String),
          graphite_service_prefix Nullable(String),
          updated_at DateTime
        )
        ENGINE = ReplacingMergeTree(updated_at)
        ORDER BY (interface_id)
        """
    )


def truncate_table(ch: ClickHouseHTTP, full_name: str) -> None:
    if table_exists(ch, full_name):
        ch.execute(f"TRUNCATE TABLE {full_name}")


def swap_in(ch: ClickHouseHTTP, new_table: str, target_table: str) -> None:
    old_table = target_table + "__old"
    ch.execute(f"DROP TABLE IF EXISTS {old_table}")
    if table_exists(ch, target_table):
        ch.execute(f"RENAME TABLE {target_table} TO {old_table}, {new_table} TO {target_table}")
        ch.execute(f"DROP TABLE IF EXISTS {old_table}")
    else:
        ch.execute(f"RENAME TABLE {new_table} TO {target_table}")


def build_service_map() -> Tuple[Dict[Tuple[int, str], NetworkServiceDevice], List[Tuple[int, str]]]:
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


class Command(BaseCommand):
    help = "Export NetBox interface labels to ClickHouse for ad-hoc querying"

    def add_arguments(self, parser):
        sidekick_config = settings.PLUGINS_CONFIG.get('sidekick', {})

        parser.add_argument(
            "--clickhouse-url",
            default=sidekick_config.get('clickhouse_url') or os.getenv("CLICKHOUSE_URL", "http://127.0.0.1:8123"),
            help="ClickHouse HTTP URL (default: http://127.0.0.1:8123)",
        )
        parser.add_argument(
            "--clickhouse-user",
            default=sidekick_config.get('clickhouse_user') or os.getenv("CLICKHOUSE_USER", ""),
            help="ClickHouse user (default: env CLICKHOUSE_USER)",
        )
        parser.add_argument(
            "--clickhouse-password",
            default=sidekick_config.get('clickhouse_password') or os.getenv("CLICKHOUSE_PASSWORD", ""),
            help="ClickHouse password (default: env CLICKHOUSE_PASSWORD)",
        )
        parser.add_argument(
            "--database",
            default=sidekick_config.get('clickhouse_database') or
            os.getenv("CLICKHOUSE_DATABASE") or
            os.getenv("CLICKHOUSE_NETFLOW_DATABASE") or
            "pmacct",
            help="ClickHouse database (default: env CLICKHOUSE_DATABASE or CLICKHOUSE_NETFLOW_DATABASE or pmacct)",
        )
        parser.add_argument(
            "--table",
            default=sidekick_config.get('clickhouse_labels_table') or
            os.getenv("CLICKHOUSE_LABELS_TABLE", "dim_interface_labels"),
            help="Target table name (default: dim_interface_labels)",
        )
        parser.add_argument(
            "--batch-size",
            type=int,
            default=5000,
            help="Insert batch size (default: 5000)",
        )
        parser.add_argument(
            "--no-swap",
            action="store_true",
            help="Insert into the target table directly (skip staging+swap)",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Build rows but do not write to ClickHouse",
        )
        parser.add_argument(
            "--verbose",
            action="store_true",
            help="Print progress and success messages",
        )

    def handle(self, *args, **options):
        sidekick_config = settings.PLUGINS_CONFIG.get('sidekick', {})

        ch = ClickHouseHTTP(
            base_url=options["clickhouse_url"],
            user=sidekick_config.get('clickhouse_user') or os.getenv("CLICKHOUSE_USER", ""),
            password=sidekick_config.get('clickhouse_password') or os.getenv("CLICKHOUSE_PASSWORD", ""),
            database=options["database"],
        )

        db = options["database"]
        target_table = f"{db}.{options['table']}"
        use_swap = not options["no_swap"]
        insert_table = target_table

        if not options["dry_run"]:
            if use_swap:
                insert_table = target_table + "__new"
                ensure_table(ch, insert_table)
                truncate_table(ch, insert_table)
            else:
                ensure_table(ch, target_table)

        service_map, duplicates = build_service_map()
        if duplicates and options['verbose']:
            self.stdout.write(
                f"WARNING: {len(duplicates)} duplicate NetworkServiceDevice mappings found; using first instance."
            )

        rows: List[Dict[str, Any]] = []
        count = 0

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
                    "updated_at": now_utc_str(),
                }
            )
            count += 1

            if not options["dry_run"] and len(rows) >= options["batch_size"]:
                self._flush_rows(ch, insert_table, rows)
                rows = []

        if rows and not options["dry_run"]:
            self._flush_rows(ch, insert_table, rows)

        if not options["dry_run"] and use_swap:
            swap_in(ch, insert_table, target_table)

        if options["dry_run"]:
            self.stdout.write(f"Dry run complete. Would export {count:,} interfaces.")
        elif options["verbose"]:
            self.stdout.write(f"Exported {count:,} interfaces to {target_table}.")

    def _flush_rows(self, ch: ClickHouseHTTP, target_table: str, rows: List[Dict[str, Any]]) -> None:
        ch.insert_json_each_row(target_table, rows)
