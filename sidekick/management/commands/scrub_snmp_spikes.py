"""
Django management command: scrub_snmp_spikes

Detects and (optionally) neutralizes SNMP counter-reset spikes in the
ClickHouse ``nic_deltas_5m`` table.

Background
----------
``sidekick.management.commands.update_interfaces`` polls 64-bit SNMP counters
(ifHCInOctets / ifHCOutOctets / packets / errors) every ~5 minutes and stores a
per-second ``delta`` in ``nic_deltas_5m``.  When a device reboots or an interface
flaps, the counter resets to a small value, so ``current - previous`` becomes a
large negative number.  Divided by the poll interval this renders as a
multi-Tb/s negative spike in Grafana (e.g. -4.4 Tb/s in / -18 Tb/s out).

As of 2026-07-13, ``update_interfaces`` skips emitting a delta when a counter
goes backwards, and the ``nic_metrics_unified`` view clamps negatives to zero
(``greatest(delta, 0)``) at read time.  This command handles the *historical*
bad rows that were written before those fixes existed.

Safety
------
* **DRY RUN by default.**  Without ``--apply`` the command only reports.
* ``--apply`` issues ``ALTER TABLE ... UPDATE`` mutations that set ``delta = 0``
  on the offending rows.  This is a row *update*, not a delete — no data is
  removed, only the impossible negative rate is zeroed.
* ``--confirm`` is required *with* ``--apply`` as a second confirmation gate.

Usage
-----
    # Dry run — report spikes from the last 30 days (default window)
    python3 manage.py scrub_snmp_spikes

    # Dry run over a specific window
    python3 manage.py scrub_snmp_spikes --since "2026-07-01 00:00:00"

    # Dry run for one interface
    python3 manage.py scrub_snmp_spikes --interface-id 42

    # Apply (mutate data) — requires both flags
    python3 manage.py scrub_snmp_spikes --apply --confirm

    # Also neutralize absurd POSITIVE spikes above a physical ceiling.
    # --max-bps is in bits/sec; the default 1 Tb/s catches anything that could
    # not possibly come from a single interface in this environment.
    python3 manage.py scrub_snmp_spikes --apply --confirm --positive --max-bps 1000000000000
"""

import os
from datetime import datetime, timezone

from django.conf import settings
from django.core.management.base import BaseCommand

from sidekick.utils.clickhouse import ClickHouseHTTP


# Metrics stored in nic_deltas_5m are all derived from monotonically-increasing
# SNMP counters, so a negative per-second delta is ALWAYS invalid.
COUNTER_METRICS = (
    'in_octets',
    'out_octets',
    'in_unicast_packets',
    'out_unicast_packets',
    'in_nunicast_packets',
    'out_nunicast_packets',
    'in_errors',
    'out_errors',
)

METRIC_LIST_SQL = ", ".join("'" + m + "'" for m in COUNTER_METRICS)


class Command(BaseCommand):
    help = (
        "Detect and optionally neutralize SNMP counter-reset spikes "
        "(negative / absurd deltas) in ClickHouse nic_deltas_5m."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--since', default=None,
            help='Only consider rows with ts >= this value (UTC, '
                 'e.g. "2026-07-01 00:00:00"). Defaults to 30 days ago.')
        parser.add_argument(
            '--until', default=None,
            help='Only consider rows with ts < this value (UTC).')
        parser.add_argument(
            '--interface-id', type=int, default=None,
            help='Restrict to a single NetBox interface_id.')
        parser.add_argument(
            '--source', default=None,
            help="Restrict to a delta source (e.g. 'live_delta', 'legacy_delta').")
        parser.add_argument(
            '--positive', action='store_true',
            help='Also flag absurd POSITIVE deltas above --max-bps.')
        parser.add_argument(
            '--max-bps', type=int, default=1_000_000_000_000,
            help='Positive-spike ceiling in bits/sec (default 1 Tb/s). '
                 'Only used with --positive. The delta column is bytes/sec, '
                 'so this is converted internally (÷8).')
        parser.add_argument(
            '--limit', type=int, default=50,
            help='Max spike rows to display in the report (default 50).')
        parser.add_argument(
            '--apply', action='store_true',
            help='Actually mutate data (ALTER TABLE ... UPDATE). '
                 'Without this flag the command is a pure dry-run.')
        parser.add_argument(
            '--confirm', action='store_true',
            help='Second confirmation gate required when --apply is used.')
        parser.add_argument(
            '--database', default=None,
            help='ClickHouse database (defaults to sidekick settings / pmacct).')

    # ------------------------------------------------------------------ #
    # ClickHouse connection
    # ------------------------------------------------------------------ #
    def _get_client(self, database):
        cfg = settings.PLUGINS_CONFIG.get('sidekick', {})
        ch_url = cfg.get('clickhouse_url') or os.getenv('CLICKHOUSE_URL')
        ch_user = cfg.get('clickhouse_user') or os.getenv('CLICKHOUSE_USER', '')
        ch_password = cfg.get('clickhouse_password') or os.getenv('CLICKHOUSE_PASSWORD', '')
        ch_db = database or cfg.get('clickhouse_database') \
            or os.getenv('CLICKHOUSE_DATABASE') \
            or os.getenv('CLICKHOUSE_NETFLOW_DATABASE') or 'pmacct'
        if not ch_url:
            raise SystemExit(
                "ERROR: no ClickHouse URL configured "
                "(PLUGINS_CONFIG['sidekick']['clickhouse_url'] or CLICKHOUSE_URL env).")
        return ClickHouseHTTP(base_url=ch_url, user=ch_user, password=ch_password, database=ch_db), ch_db

    # ------------------------------------------------------------------ #
    # WHERE-clause builder
    # ------------------------------------------------------------------ #
    def _where(self, since, until, interface_id, source):
        clauses = [f"metric IN ({METRIC_LIST_SQL})"]
        if since:
            clauses.append(f"ts >= '{since}'")
        if until:
            clauses.append(f"ts < '{until}'")
        if interface_id is not None:
            clauses.append(f"interface_id = {int(interface_id)}")
        if source:
            # source is LowCardinality(String); quote it.
            s = str(source).replace("'", "''")
            clauses.append(f"source = '{s}'")
        return " AND ".join(clauses)

    # ------------------------------------------------------------------ #
    # handle()
    # ------------------------------------------------------------------ #
    def handle(self, *args, **options):
        since = options['since'] or (
            datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        )  # default: all data — but we narrow below to 30 days for the report
        if not options['since']:
            # Default window: last 30 days, to keep the report focused.
            since = "now() - INTERVAL 30 DAY"

        until = options['until']
        interface_id = options['interface_id']
        source = options['source']
        positive = options['positive']
        max_bps = options['max_bps']
        limit = options['limit']
        apply = options['apply']
        confirm = options['confirm']

        ch, ch_db = self._get_client(options['database'])
        where = self._where(since, until, interface_id, source)

        self.stdout.write(self.style.MIGRATE_HEADING(
            f"Scrub SNMP counter-reset spikes — database: {ch_db}"))
        self.stdout.write(f"WHERE: {where}")
        self.stdout.write(f"Mode: {'APPLY (mutate)' if apply else 'DRY RUN (read-only)'}")
        if apply and not confirm:
            self.stdout.write(self.style.ERROR(
                "ERROR: --apply requires --confirm as a second gate. Aborting."))
            return
        self.stdout.write("")

        # ------------------------------------------------------------------
        # 1. Negative spikes (always invalid for counter-derived rates)
        # ------------------------------------------------------------------
        neg_count_q = (
            f"SELECT count() FROM nic_deltas_5m "
            f"WHERE {where} AND delta < 0"
        )
        neg_count = ch.execute_scalar_u8(neg_count_q)
        self.stdout.write(self.style.WARNING(
            f"Negative-delta spike rows: {neg_count}"))

        if neg_count:
            neg_sample_q = (
                f"SELECT ts, interface_id, member_slug, service_slug, "
                f"metric, delta, source "
                f"FROM nic_deltas_5m "
                f"WHERE {where} AND delta < 0 "
                f"ORDER BY ts DESC "
                f"LIMIT {int(limit)}"
            )
            self.stdout.write("  Sample (most recent first):")
            self.stdout.write(f"  {neg_sample_q}")
            rows = ch.execute(neg_sample_q + "\nFORMAT TabSeparated")
            self.stdout.write(rows)
            self.stdout.write("")

        # ------------------------------------------------------------------
        # 2. Positive spikes (optional, above a physical ceiling)
        # ------------------------------------------------------------------
        pos_count = 0
        if positive:
            max_bytes_per_sec = max_bps / 8
            pos_count_q = (
                f"SELECT count() FROM nic_deltas_5m "
                f"WHERE {where} AND delta > {max_bytes_per_sec}"
            )
            pos_count = ch.execute_scalar_u8(pos_count_q)
            self.stdout.write(self.style.WARNING(
                f"Positive-delta spike rows (> {max_bps} bps / "
                f"{max_bytes_per_sec:.0f} B/s): {pos_count}"))
            if pos_count:
                pos_sample_q = (
                    f"SELECT ts, interface_id, member_slug, service_slug, "
                    f"metric, delta, source "
                    f"FROM nic_deltas_5m "
                    f"WHERE {where} AND delta > {max_bytes_per_sec} "
                    f"ORDER BY delta DESC "
                    f"LIMIT {int(limit)}"
                )
                self.stdout.write("  Sample (largest first):")
                self.stdout.write(f"  {pos_sample_q}")
                self.stdout.write(ch.execute(pos_sample_q + "\nFORMAT TabSeparated"))
                self.stdout.write("")

        # ------------------------------------------------------------------
        # 3. Apply (neutralize via ALTER TABLE ... UPDATE)
        # ------------------------------------------------------------------
        if not apply:
            self.stdout.write(self.style.MIGRATE_HEADING(
                "Dry run complete. No rows were modified."))
            if neg_count or pos_count:
                self.stdout.write(
                    "Re-run with --apply --confirm to set these delta values to 0.")
            return

        if not (neg_count or pos_count):
            self.stdout.write(self.style.SUCCESS(
                "No spikes found. Nothing to do."))
            return

        mutations = []
        if neg_count:
            mutations.append((
                "negative spikes -> 0",
                f"ALTER TABLE nic_deltas_5m UPDATE delta = 0 "
                f"WHERE {where} AND delta < 0"
            ))
        if positive and pos_count:
            max_bytes_per_sec = max_bps / 8
            mutations.append((
                f"positive spikes (> {max_bps} bps) -> 0",
                f"ALTER TABLE nic_deltas_5m UPDATE delta = 0 "
                f"WHERE {where} AND delta > {max_bytes_per_sec}"
            ))

        for label, stmt in mutations:
            self.stdout.write(self.style.WARNING(f"Applying: {label}"))
            self.stdout.write(f"  {stmt}")
            ch.execute(stmt)
            self.stdout.write(self.style.SUCCESS("  submitted."))

        self.stdout.write("")
        self.stdout.write(self.style.MIGRATE_HEADING(
            "Mutations submitted. ClickHouse processes them asynchronously."))
        self.stdout.write(
            "Check progress with: "
            "SELECT database, table, mutation_id, command, is_done, "
            "parts_to_do, latest_fail_reason "
            "FROM clusterAllReplicas(system.mutations) "
            "WHERE table = 'nic_deltas_5m' AND NOT is_done "
            "ORDER BY create_time DESC")
        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS(
            "Note: the nic_metrics_unified view already clamps negatives to 0 "
            "at read time (greatest(delta, 0)), so Grafana graphs will already "
            "reflect the cleaned values without waiting for the mutations."))
