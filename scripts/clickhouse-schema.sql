-- ClickHouse schema for NetBox-sidekick NIC counters and deltas.
-- Adjust database name before running (defaults assume pmacct).

CREATE TABLE IF NOT EXISTS pmacct.nic_counters_raw
(
  ts DateTime,
  interface_id UInt32,
  admin_status UInt8,
  oper_status UInt8,
  out_octets UInt64,
  in_octets UInt64,
  out_unicast_packets UInt64,
  in_unicast_packets UInt64,
  out_nunicast_packets UInt64,
  in_nunicast_packets UInt64,
  out_errors UInt64,
  in_errors UInt64,
  in_rate Int64,
  out_rate Int64
)
ENGINE = MergeTree
PARTITION BY toYYYYMM(ts)
ORDER BY (interface_id, ts)
TTL ts + INTERVAL 5 YEAR;

-- Table for historical Graphite deltas (Legacy Data).
CREATE TABLE IF NOT EXISTS pmacct.nic_deltas_5m
(
  ts DateTime,
  interface_id Nullable(UInt32),
  accounting_source_id Nullable(UInt32),
  metric LowCardinality(String),
  delta Float64
)
ENGINE = ReplacingMergeTree
PARTITION BY toYYYYMM(ts)
ORDER BY (interface_id, accounting_source_id, metric, ts)
TTL ts + INTERVAL 5 YEAR;

CREATE TABLE IF NOT EXISTS pmacct.nic_deltas_1h
(
  ts DateTime,
  interface_id Nullable(UInt32),
  accounting_source_id Nullable(UInt32),
  metric LowCardinality(String),
  delta Float64
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
            CAST(NULL, 'Nullable(UInt32)') as accounting_source_id,
            in_octets,
            out_octets,
            in_rate,
            out_rate,
            lagInFrame(in_octets) OVER (PARTITION BY interface_id ORDER BY ts ASC ROWS BETWEEN 1 PRECEDING AND 1 PRECEDING) as prev_in,
            lagInFrame(out_octets) OVER (PARTITION BY interface_id ORDER BY ts ASC ROWS BETWEEN 1 PRECEDING AND 1 PRECEDING) as prev_out,
            lagInFrame(ts) OVER (PARTITION BY interface_id ORDER BY ts ASC ROWS BETWEEN 1 PRECEDING AND 1 PRECEDING) as prev_ts
        FROM pmacct.nic_counters_raw
    )
SELECT
    ts,
    interface_id,
    accounting_source_id,
    'in_octets' as metric,
    if(in_rate > 0, CAST(in_rate, 'Float64'),
       if(prev_ts != toDateTime(0) AND ts > prev_ts AND in_octets >= prev_in,
          (in_octets - prev_in) / (toUnixTimestamp(ts) - toUnixTimestamp(prev_ts)), 0)
    ) as delta,
    if(in_rate > 0, 'raw_device', 'raw_calc') as source
FROM raw_with_lag
UNION ALL
SELECT
    ts,
    interface_id,
    accounting_source_id,
    'out_octets' as metric,
    if(out_rate > 0, CAST(out_rate, 'Float64'),
       if(prev_ts != toDateTime(0) AND ts > prev_ts AND out_octets >= prev_out,
          (out_octets - prev_out) / (toUnixTimestamp(ts) - toUnixTimestamp(prev_ts)), 0)
    ) as delta,
    if(out_rate > 0, 'raw_device', 'raw_calc') as source
FROM raw_with_lag
UNION ALL
SELECT
    ts,
    interface_id,
    accounting_source_id,
    metric,
    delta,
    'legacy_delta' as source
FROM pmacct.nic_deltas_5m;
