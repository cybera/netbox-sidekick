# Graphite to ClickHouse Migration

This document outlines the architecture and process for migrating NetBox-sidekick metrics from Graphite/Whisper to ClickHouse.

## System Overview

Historically, NetBox-sidekick metrics were stored in Graphite (Whisper files) as derivatives (deltas). The new system stores **raw SNMP counters** in ClickHouse (`nic_counters_raw`) and calculates deltas/rates dynamically at query time using a Unified View.

### ClickHouse Schema

- `nic_counters_raw`: Stores raw SNMP counter values.
- `nic_deltas_5m`: Stores **historical** 5-minute rates migrated from Whisper. This table is *not* populated with new data.
- `dim_interface_labels`: Stores metadata about interfaces (device name, member name, etc.) for easy querying.
- `nic_metrics_unified`: A **Unified View** that seamlessly combines:
    1.  New rates calculated on-the-fly from `nic_counters_raw` (using Window Functions).
    2.  Legacy rates from `nic_deltas_5m`.

## Migration Process

### 1. Apply ClickHouse Schema
The schema is managed by the Ansible role in `netflow/ansible/netflow`. 
Run the playbook to ensure the tables and views are created:

```bash
ansible-playbook -i production site.yml --tags clickhouse
```

Alternatively, apply the schema manually using `scripts/clickhouse-schema.sql`.

### 2. Export Interface Labels
Export interface metadata from NetBox to ClickHouse. This is required for matching Whisper files to NetBox IDs.

```bash
python manage.py export_clickhouse_interface_labels
```

### 3. Migrate Whisper Data
Use the migration script to load historical data from Whisper files into ClickHouse.

```bash
python manage.py migrate_graphite_to_clickhouse --whisper-dir /var/lib/graphite/whisper
```

*Note: Ensure `CLICKHOUSE_URL`, `CLICKHOUSE_USER`, and `CLICKHOUSE_PASSWORD` environment variables are set.*

The migration script supports:
- **Parallel Workers**: Use `--workers N` to speed up processing.
- **Idempotency**: It checks ClickHouse for existing data and skips files/points that have already been migrated.
- **Resumability**: You can stop and restart the script at any time.

### 4. Update Metric Collection
Ensure `update_interfaces.py` is configured to send data to ClickHouse. This is usually handled via environment variables or `PLUGINS_CONFIG`.

## Day-to-Day Management

### Verifying Data Flow
You can check if data is arriving in ClickHouse using `clickhouse-client`:

```sql
-- Check raw counters
SELECT * FROM pmacct.nic_counters_raw ORDER BY ts DESC LIMIT 10;

-- Check unified view (Calculated Rates + Legacy)
SELECT * FROM pmacct.nic_metrics_unified ORDER BY ts DESC LIMIT 10;
```

### Adding New Devices
When new devices are added to NetBox, the `export_clickhouse_interface_labels` command should be run to update the dimension table. This is ideally automated via a cron job.

## Decommissioning Graphite

Once ClickHouse data is verified and Grafana dashboards are updated:

1. Remove `graphite_host` from `PLUGINS_CONFIG['sidekick']`.
2. Disable the `graphyte` dependency in `requirements.txt`.
3. Stop and disable the Carbon/Graphite services on the NetBox server.
4. Remove the legacy Graphite migration logic from `update_interfaces.py`.
