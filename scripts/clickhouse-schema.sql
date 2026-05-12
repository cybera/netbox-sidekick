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
  delta Float64 CODEC(ZSTD(3))
)
ENGINE = ReplacingMergeTree
PARTITION BY toYYYYMM(ts)
ORDER BY (interface_id, accounting_source_id, metric, ts)
TTL ts + INTERVAL 5 YEAR;

CREATE TABLE IF NOT EXISTS pmacct.nic_deltas_1h
(
  ts DateTime CODEC(Delta, ZSTD(3)),
  interface_id UInt32 DEFAULT 0 CODEC(T64, ZSTD(3)),
  accounting_source_id UInt32 DEFAULT 0 CODEC(T64, ZSTD(3)),
  member_slug LowCardinality(String) DEFAULT '' CODEC(ZSTD(3)),
  service_slug LowCardinality(String) DEFAULT '' CODEC(ZSTD(3)),
  metric LowCardinality(String) CODEC(ZSTD(3)),
  delta Float64 CODEC(ZSTD(3))
)
ENGINE = ReplacingMergeTree
PARTITION BY toYYYYMM(ts)
ORDER BY (interface_id, accounting_source_id, metric, ts)
TTL ts + INTERVAL 10 YEAR;

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
  updated_at DateTime
)
ENGINE = ReplacingMergeTree(updated_at)
ORDER BY (accounting_source_id);

-- Unified View for seamless querying of legacy and new data.
-- Calculates rates dynamically from raw counters using Window Functions.
CREATE OR REPLACE VIEW pmacct.nic_metrics_unified AS
WITH
    raw_with_lag AS (
        SELECT
            ts,
            interface_id,
            toUInt32(0) as accounting_source_id,
            member_slug,
            service_slug,
            in_octets, out_octets,
            in_unicast_packets, out_unicast_packets,
            in_nunicast_packets, out_nunicast_packets,
            in_errors, out_errors,
            in_rate, out_rate,
            lagInFrame(ts) OVER (PARTITION BY interface_id ORDER BY ts ASC ROWS BETWEEN 1 PRECEDING AND 1 PRECEDING) as prev_ts,
            lagInFrame(in_octets) OVER (PARTITION BY interface_id ORDER BY ts ASC ROWS BETWEEN 1 PRECEDING AND 1 PRECEDING) as prev_in_octets,
            lagInFrame(out_octets) OVER (PARTITION BY interface_id ORDER BY ts ASC ROWS BETWEEN 1 PRECEDING AND 1 PRECEDING) as prev_out_octets,
            lagInFrame(in_unicast_packets) OVER (PARTITION BY interface_id ORDER BY ts ASC ROWS BETWEEN 1 PRECEDING AND 1 PRECEDING) as prev_in_ucast,
            lagInFrame(out_unicast_packets) OVER (PARTITION BY interface_id ORDER BY ts ASC ROWS BETWEEN 1 PRECEDING AND 1 PRECEDING) as prev_out_ucast,
            lagInFrame(in_nunicast_packets) OVER (PARTITION BY interface_id ORDER BY ts ASC ROWS BETWEEN 1 PRECEDING AND 1 PRECEDING) as prev_in_nucast,
            lagInFrame(out_nunicast_packets) OVER (PARTITION BY interface_id ORDER BY ts ASC ROWS BETWEEN 1 PRECEDING AND 1 PRECEDING) as prev_out_nucast,
            lagInFrame(in_errors) OVER (PARTITION BY interface_id ORDER BY ts ASC ROWS BETWEEN 1 PRECEDING AND 1 PRECEDING) as prev_in_errors,
            lagInFrame(out_errors) OVER (PARTITION BY interface_id ORDER BY ts ASC ROWS BETWEEN 1 PRECEDING AND 1 PRECEDING) as prev_out_errors
        FROM pmacct.nic_counters_raw
    )
SELECT
    ts, interface_id, accounting_source_id, member_slug, service_slug, 'in_octets' as metric,
    if(in_rate > 0, CAST(in_rate, 'Float64'),
       if(prev_ts != toDateTime(0) AND ts > prev_ts AND in_octets >= prev_in_octets,
          (in_octets - prev_in_octets) / (toUnixTimestamp(ts) - toUnixTimestamp(prev_ts)), 0)
    ) as delta,
    if(in_rate > 0, 'raw_device', 'raw_calc') as source
FROM raw_with_lag
UNION ALL
SELECT
    ts, interface_id, accounting_source_id, member_slug, service_slug, 'out_octets' as metric,
    if(out_rate > 0, CAST(out_rate, 'Float64'),
       if(prev_ts != toDateTime(0) AND ts > prev_ts AND out_octets >= prev_out_octets,
          (out_octets - prev_out_octets) / (toUnixTimestamp(ts) - toUnixTimestamp(prev_ts)), 0)
    ) as delta,
    if(out_rate > 0, 'raw_device', 'raw_calc') as source
FROM raw_with_lag
UNION ALL
SELECT
    ts, interface_id, accounting_source_id, member_slug, service_slug, 'in_unicast_packets' as metric,
    if(prev_ts != toDateTime(0) AND ts > prev_ts AND in_unicast_packets >= prev_in_ucast,
       (in_unicast_packets - prev_in_ucast) / (toUnixTimestamp(ts) - toUnixTimestamp(prev_ts)), 0) as delta,
    'raw_calc' as source
FROM raw_with_lag
UNION ALL
SELECT
    ts, interface_id, accounting_source_id, member_slug, service_slug, 'out_unicast_packets' as metric,
    if(prev_ts != toDateTime(0) AND ts > prev_ts AND out_unicast_packets >= prev_out_ucast,
       (out_unicast_packets - prev_out_ucast) / (toUnixTimestamp(ts) - toUnixTimestamp(prev_ts)), 0) as delta,
    'raw_calc' as source
FROM raw_with_lag
UNION ALL
SELECT
    ts, interface_id, accounting_source_id, member_slug, service_slug, 'in_nunicast_packets' as metric,
    if(prev_ts != toDateTime(0) AND ts > prev_ts AND in_nunicast_packets >= prev_in_nucast,
       (in_nunicast_packets - prev_in_nucast) / (toUnixTimestamp(ts) - toUnixTimestamp(prev_ts)), 0) as delta,
    'raw_calc' as source
FROM raw_with_lag
UNION ALL
SELECT
    ts, interface_id, accounting_source_id, member_slug, service_slug, 'out_nunicast_packets' as metric,
    if(prev_ts != toDateTime(0) AND ts > prev_ts AND out_nunicast_packets >= prev_out_nucast,
       (out_nunicast_packets - prev_out_nucast) / (toUnixTimestamp(ts) - toUnixTimestamp(prev_ts)), 0) as delta,
    'raw_calc' as source
FROM raw_with_lag
UNION ALL
SELECT
    ts, interface_id, accounting_source_id, member_slug, service_slug, 'in_errors' as metric,
    if(prev_ts != toDateTime(0) AND ts > prev_ts AND in_errors >= prev_in_errors,
       (in_errors - prev_in_errors) / (toUnixTimestamp(ts) - toUnixTimestamp(prev_ts)), 0) as delta,
    'raw_calc' as source
FROM raw_with_lag
UNION ALL
SELECT
    ts, interface_id, accounting_source_id, member_slug, service_slug, 'out_errors' as metric,
    if(prev_ts != toDateTime(0) AND ts > prev_ts AND out_errors >= prev_out_errors,
       (out_errors - prev_out_errors) / (toUnixTimestamp(ts) - toUnixTimestamp(prev_ts)), 0) as delta,
    'raw_calc' as source
FROM raw_with_lag
UNION ALL
SELECT
    ts, interface_id, accounting_source_id, member_slug, service_slug, metric, delta, 'legacy_delta' as source
FROM pmacct.nic_deltas_5m
WHERE (interface_id > 0 AND member_slug = '') OR interface_id = 0;

CREATE OR REPLACE VIEW pmacct.v_snmp_mapping AS
SELECT
    device_id,
    argMax(snmp_index, ts) AS snmp_index,
    interface_id
FROM pmacct.nic_counters_raw
GROUP BY device_id, interface_id;
