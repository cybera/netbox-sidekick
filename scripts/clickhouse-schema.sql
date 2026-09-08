-- ClickHouse schema for NetBox-sidekick NIC counters and deltas.
-- Adjust database name before running (defaults assume pmacct).

CREATE TABLE IF NOT EXISTS pmacct.nic_counters_raw
(
  ts DateTime CODEC(Delta, ZSTD(3)),
  interface_id UInt32 CODEC(T64, ZSTD(3)),
  device_id UInt32 CODEC(T64, ZSTD(3)),
  snmp_index UInt32 CODEC(T64, ZSTD(3)),
  member_slug LowCardinality(String) DEFAULT '' CODEC(ZSTD(3)),
  service_slug LowCardinality(String) DEFAULT '' CODEC(ZSTD(3)),
  admin_status UInt8 CODEC(ZSTD(3)),
  oper_status UInt8 CODEC(ZSTD(3)),
  out_octets UInt64 CODEC(T64, ZSTD(3)),
  in_octets UInt64 CODEC(T64, ZSTD(3)),
  out_unicast_packets UInt64 CODEC(T64, ZSTD(3)),
  in_unicast_packets UInt64 CODEC(T64, ZSTD(3)),
  out_nunicast_packets UInt64 CODEC(T64, ZSTD(3)),
  in_nunicast_packets UInt64 CODEC(T64, ZSTD(3)),
  out_errors UInt64 CODEC(T64, ZSTD(3)),
  in_errors UInt64 CODEC(T64, ZSTD(3)),
  in_rate Int64 CODEC(T64, ZSTD(3)),
  out_rate Int64 CODEC(T64, ZSTD(3))
)
ENGINE = MergeTree
PARTITION BY toYYYYMM(ts)
ORDER BY (interface_id, ts)
TTL ts + INTERVAL 5 YEAR;

-- Table for historical Graphite deltas (Legacy Data & SCU/DCU).
CREATE TABLE IF NOT EXISTS pmacct.nic_deltas_5m
(
  ts DateTime CODEC(Delta, ZSTD(3)),
  interface_id UInt32 DEFAULT 0 CODEC(T64, ZSTD(3)),
  accounting_source_id UInt32 DEFAULT 0 CODEC(T64, ZSTD(3)),
  member_slug LowCardinality(String) DEFAULT '' CODEC(ZSTD(3)),
  service_slug LowCardinality(String) DEFAULT '' CODEC(ZSTD(3)),
  metric LowCardinality(String) CODEC(ZSTD(3)),
  delta Float64 CODEC(ZSTD(3)),
  source LowCardinality(String) DEFAULT 'legacy_delta' CODEC(ZSTD(3))
)
ENGINE = ReplacingMergeTree
PARTITION BY toYYYYMM(ts)
ORDER BY (interface_id, accounting_source_id, metric, ts)
TTL ts + INTERVAL 5 YEAR;

CREATE TABLE IF NOT EXISTS pmacct.dim_interface_labels
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
ORDER BY (interface_id);

CREATE TABLE IF NOT EXISTS pmacct.dim_accounting_sources
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
ORDER BY (accounting_source_id);

-- Central member dimension: one row per member (Tenant) with traffic cap.
-- Populated by export_data_to_clickhouse.py from NetworkService + AccountingProfile.
-- Referenced by dim_accounting_sources, dim_member_prefixes, and FNM attack events.
CREATE TABLE IF NOT EXISTS pmacct.dim_members
(
  member_id UInt32,
  member_name String,
  member_slug String,
  traffic_cap_mbps Nullable(UInt32),
  updated_at DateTime
)
ENGINE = ReplacingMergeTree(updated_at)
ORDER BY (member_slug);

-- Prefix → member mapping: one row per (prefix, member) pair.
-- Populated from NetworkService.get_prefixes() for active transit/c-all services.
-- FNM attack events JOIN on this table to attribute an attacked IP to a member
-- via isIPAddressInRange(ip, prefix) or IPv4CIDRToRange().
CREATE TABLE IF NOT EXISTS pmacct.dim_member_prefixes
(
  prefix String,
  member_slug String,
  updated_at DateTime
)
ENGINE = ReplacingMergeTree(updated_at)
ORDER BY (prefix, member_slug);

-- ClickHouse dictionaries for IP → member lookup (used by Grafana dashboards
-- and FNM attack event attribution). The ip_trie layout enables O(log N)
-- CIDR prefix lookups via dictGet(). Refreshed every 5-60 minutes from
-- dim_member_prefixes + dim_members, which are populated by the sidekick
-- export_data_to_clickhouse management command.
CREATE DICTIONARY IF NOT EXISTS pmacct.dict_member_prefixes
(
  prefix String,
  member_slug String
)
PRIMARY KEY prefix
LAYOUT(IP_TRIE())
SOURCE(CLICKHOUSE(QUERY 'SELECT prefix, member_slug FROM pmacct.dim_member_prefixes'))
LIFETIME(MIN 300 MAX 3600);

CREATE DICTIONARY IF NOT EXISTS pmacct.dict_members
(
  member_slug String,
  member_name String,
  traffic_cap_mbps Nullable(UInt32)
)
PRIMARY KEY member_slug
LAYOUT(HASHED())
SOURCE(CLICKHOUSE(QUERY 'SELECT member_slug, member_name, traffic_cap_mbps FROM pmacct.dim_members'))
LIFETIME(MIN 300 MAX 3600);

-- Unified View for seamless querying of legacy and new data.
-- Aggregates metrics to prevent duplication and handles multiple samples per time bucket.
CREATE OR REPLACE VIEW pmacct.nic_metrics_unified AS
SELECT
    toStartOfInterval(ts, toIntervalMinute(5)) AS ts,
    interface_id,
    accounting_source_id,
    member_slug,
    service_slug,
    metric,
    avg(delta) AS delta,
    any(source) AS source
FROM pmacct.nic_deltas_5m
GROUP BY ts, interface_id, accounting_source_id, member_slug, service_slug, metric;

CREATE OR REPLACE VIEW pmacct.v_snmp_mapping AS
SELECT
    device_id,
    argMax(snmp_index, ts) AS snmp_index,
    interface_id
FROM pmacct.nic_counters_raw
GROUP BY device_id, interface_id;
