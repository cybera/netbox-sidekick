#!/usr/bin/env python3

import os
from typing import Any, Dict, List

from django.conf import settings
from django.core.management.base import BaseCommand

from sidekick.utils.clickhouse import ClickHouseHTTP, now_utc_str
from sidekick.utils.dims import (
    build_accounting_source_rows,
    build_interface_label_rows,
    build_member_rows,
)


def sql_str(v: str) -> str:
    return "'" + v.replace("'", "''") + "'"


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
          device_ip String,
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


def ensure_accounting_table(ch: ClickHouseHTTP, full_name: str) -> None:
    ch.execute(
        f"""
        CREATE TABLE IF NOT EXISTS {full_name}
        (
          accounting_source_id UInt32,
          device_id UInt32,
          device_name String,
          source_name String,
          destination_name String,
          graphite_prefix String,
          member_name Nullable(String),
          member_slug Nullable(String),
          updated_at DateTime
        )
        ENGINE = ReplacingMergeTree(updated_at)
        ORDER BY (accounting_source_id)
        """
    )


def ensure_members_table(ch: ClickHouseHTTP, full_name: str) -> None:
    ch.execute(
        f"""
        CREATE TABLE IF NOT EXISTS {full_name}
        (
          member_id UInt32,
          member_name String,
          member_slug String,
          traffic_cap_mbps Nullable(UInt32),
          updated_at DateTime
        )
        ENGINE = ReplacingMergeTree(updated_at)
        ORDER BY (member_slug)
        """
    )


def ensure_member_prefixes_table(ch: ClickHouseHTTP, full_name: str) -> None:
    ch.execute(
        f"""
        CREATE TABLE IF NOT EXISTS {full_name}
        (
          prefix String,
          member_slug String,
          updated_at DateTime
        )
        ENGINE = ReplacingMergeTree(updated_at)
        ORDER BY (prefix, member_slug)
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


class Command(BaseCommand):
    help = "Export NetBox dimension data to ClickHouse (interface labels, accounting sources, members, member prefixes). Row-building lives in sidekick.utils.dims so the push and the netflow-side pull (via the clickhouse-dims API endpoint) produce identical rows."

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
            help=(
                "Insert into the target table directly (skip staging+swap). "
                "Only affects dim_interface_labels and dim_accounting_sources; "
                "dim_members/dim_member_prefixes are always direct "
                "(dictionaries depend on them, which blocks RENAME)."
            ),
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
        batch_size = options["batch_size"]

        def flush_batches(table: str, rows: List[Dict[str, Any]]) -> None:
            """Stamp updated_at and insert rows in batches."""
            if options["dry_run"] or not rows:
                return
            for row in rows:
                row["updated_at"] = now_utc_str()
            for i in range(0, len(rows), batch_size):
                self._flush_rows(ch, table, rows[i:i + batch_size])

        # ------------------------------------------------------------------
        # Interface labels (dim_interface_labels)
        # ------------------------------------------------------------------
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

        rows, duplicates = build_interface_label_rows()
        if duplicates and options['verbose']:
            self.stdout.write(
                f"WARNING: {len(duplicates)} duplicate NetworkServiceDevice mappings found; using first instance."
            )
        count = len(rows)
        flush_batches(insert_table, rows)

        if not options["dry_run"] and use_swap:
            swap_in(ch, insert_table, target_table)

        # ------------------------------------------------------------------
        # Accounting sources (dim_accounting_sources)
        # ------------------------------------------------------------------
        target_acc_table = f"{db}.dim_accounting_sources"
        insert_acc_table = target_acc_table
        if not options["dry_run"]:
            if use_swap:
                insert_acc_table = target_acc_table + "__new"
                ensure_accounting_table(ch, insert_acc_table)
                truncate_table(ch, insert_acc_table)
            else:
                ensure_accounting_table(ch, target_acc_table)

        acc_rows, backfilled = build_accounting_source_rows()
        if backfilled and options['verbose']:
            self.stdout.write(f"Backfilled member info for {backfilled} AccountingSources from siblings.")
        acc_count = len(acc_rows)
        flush_batches(insert_acc_table, acc_rows)

        if not options["dry_run"] and use_swap:
            swap_in(ch, insert_acc_table, target_acc_table)

        # ------------------------------------------------------------------
        # Members + member prefixes (dim_members, dim_member_prefixes)
        #
        # dim_members: one row per member (Tenant) with current traffic cap.
        # dim_member_prefixes: one row per (prefix, member_slug) pair from
        # active transit/c-all network services. FNM attack events JOIN on
        # this table to attribute an attacked IP to a member.
        #
        # NOTE: these two tables are always refreshed with ensure+truncate+
        # insert directly into the target table — never the staging+swap
        # pattern, even with --swap (the default). The pmacct.dict_members
        # and pmacct.dict_member_prefixes dictionaries (FastNetMon attack
        # attribution, FastNetMon dashboards) declare these tables as
        # dependencies, and ClickHouse refuses to RENAME tables that have
        # dependents (HAVE_DEPENDENT_OBJECTS, code 630), which made the
        # nightly export fail after every swap attempt. Both tables are
        # tiny (<1k rows) so the non-atomic refresh is harmless: dictionary
        # readers keep serving cached values across the refresh, and both
        # dictionaries are reloaded explicitly once the insert completes.
        # ------------------------------------------------------------------
        target_members_table = f"{db}.dim_members"
        target_prefixes_table = f"{db}.dim_member_prefixes"

        if not options["dry_run"]:
            # Remove staging leftovers from the swap era: dim_members__new /
            # dim_member_prefixes__new were populated nightly by the failing
            # RENAME and are no longer used by this export.
            ch.execute(f"DROP TABLE IF EXISTS {target_members_table}__new")
            ch.execute(f"DROP TABLE IF EXISTS {target_prefixes_table}__new")
            ensure_members_table(ch, target_members_table)
            ensure_member_prefixes_table(ch, target_prefixes_table)
            truncate_table(ch, target_members_table)
            truncate_table(ch, target_prefixes_table)

        member_rows, member_prefix_rows = build_member_rows()
        member_count = len(member_rows)
        member_prefix_count = len(member_prefix_rows)
        flush_batches(target_members_table, member_rows)
        flush_batches(target_prefixes_table, member_prefix_rows)

        if not options["dry_run"]:
            # Refresh the member dictionaries immediately instead of
            # waiting out their LIFETIME (5–60 min). Missing dictionaries
            # (e.g. a fresh environment) are not an error.
            for dict_name in (f"{db}.dict_members", f"{db}.dict_member_prefixes"):
                try:
                    ch.execute(f"SYSTEM RELOAD DICTIONARY {dict_name}")
                except Exception as exc:  # noqa: BLE001 - best-effort refresh
                    if options["verbose"]:
                        self.stdout.write(
                            f"WARNING: could not reload dictionary {dict_name}: {exc}"
                        )

        if options["dry_run"]:
            self.stdout.write(
                f"Dry run complete. Would export {count:,} interfaces, "
                f"{acc_count:,} accounting sources, "
                f"{member_count:,} members, and "
                f"{member_prefix_count:,} member prefixes."
            )
        elif options["verbose"]:
            self.stdout.write(
                f"Exported {count:,} interfaces, "
                f"{acc_count:,} accounting sources, "
                f"{member_count:,} members, and "
                f"{member_prefix_count:,} member prefixes to {db}.*."
            )

    def _flush_rows(self, ch: ClickHouseHTTP, target_table: str, rows: List[Dict[str, Any]]) -> None:
        ch.insert_json_each_row(target_table, rows)
