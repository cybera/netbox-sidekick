import os
import whisper
import logging
import multiprocessing
import json
from datetime import datetime, timezone
from concurrent.futures import ProcessPoolExecutor, as_completed
from django.conf import settings
from django.core.management.base import BaseCommand
from sidekick.utils.clickhouse import ClickHouseHTTP
from dcim.models import Interface

# Configure logging for workers
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def migrate_file(file_info):
    """
    Worker function to process a single Whisper file.
    """
    full_path, iface_id, metric, ch_params, last_ts = file_info
    
    try:
        ch = ClickHouseHTTP(**ch_params)
        (start, end, step), values = whisper.fetch(full_path, 0)
        
        rows = []
        points = 0
        current_ts = start
        for val in values:
            # Skip if we already have this data or it's empty
            if val is not None and current_ts > last_ts:
                rows.append({
                    "ts": datetime.fromtimestamp(current_ts, tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
                    "interface_id": iface_id,
                    "metric": metric,
                    "delta": float(val)
                })
                points += 1
            current_ts += step
            
            if len(rows) >= 10000:
                ch.insert_json_each_row(f"{ch.database}.nic_deltas_5m", rows)
                rows = []
        
        if rows:
            ch.insert_json_each_row(f"{ch.database}.nic_deltas_5m", rows)
            
        return points, None
    except Exception as e:
        return 0, str(e)

class Command(BaseCommand):
    help = "Migrate historical data from Graphite/Whisper files to ClickHouse with idempotency"

    def add_arguments(self, parser):
        sidekick_config = settings.PLUGINS_CONFIG.get('sidekick', {})

        parser.add_argument("--whisper-dir", required=True, help="Base directory of Whisper files")
        parser.add_argument(
            "--clickhouse-url",
            default=sidekick_config.get('clickhouse_url') or os.getenv("CLICKHOUSE_URL", "http://127.0.0.1:8123"),
        )
        parser.add_argument(
            "--database",
            default=sidekick_config.get('clickhouse_database')
            or os.getenv("CLICKHOUSE_DATABASE")
            or os.getenv("CLICKHOUSE_NETFLOW_DATABASE")
            or "pmacct",
        )
        parser.add_argument("--workers", type=int, default=multiprocessing.cpu_count())
        parser.add_argument("--limit", type=int, default=0)
        parser.add_argument("--no-state-check", action="store_true", help="Skip checking ClickHouse for existing data")

    def handle(self, *args, **options):
        sidekick_config = settings.PLUGINS_CONFIG.get('sidekick', {})
        ch_params = {
            "base_url": options["clickhouse_url"],
            "user": sidekick_config.get('clickhouse_user') or os.getenv("CLICKHOUSE_USER", ""),
            "password": sidekick_config.get('clickhouse_password') or os.getenv("CLICKHOUSE_PASSWORD", ""),
            "database": options["database"],
        }
        ch = ClickHouseHTTP(**ch_params)

        self.stdout.write("Building interface mapping...")
        iface_map = {}
        for iface in Interface.objects.select_related("device"):
            dev_segment = iface.device.name.lower().replace(" ", "_").replace(".", "_").replace("(", "").replace(")", "")
            if_segment = iface.name.lower().replace("/", "-").replace(".", "_").replace("(", "").replace(")", "")
            iface_map[(dev_segment, if_segment)] = iface.id

        # High-water mark state checking
        checkpoints = {}
        if not options['no_state_check']:
            self.stdout.write("Checking ClickHouse for existing data state...")
            try:
                # Query max(ts) for each interface/metric to skip already migrated data
                query = (
                    f"SELECT interface_id, metric, toUnixTimestamp(max(ts)) "
                    f"FROM {options['database']}.nic_deltas_5m GROUP BY interface_id, metric"
                )
                # execute returns the raw response body
                raw_data = ch.execute(query + " FORMAT JSON")
                data = json.loads(raw_data)
                for row in data['data']:
                    checkpoints[(int(row[0]), row[1])] = int(row[2])
                self.stdout.write(f"Found {len(checkpoints)} existing interface/metric checkpoints.")
            except Exception as e:
                self.stdout.write(self.style.WARNING(f"Could not fetch state (normal on first run): {e}"))

        self.stdout.write(f"Scanning {options['whisper_dir']}...")
        tasks = []
        # Get the device segment from the directory name as a fallback
        dir_dev_segment = os.path.basename(options["whisper_dir"].rstrip(os.sep))

        for root, dirs, files in os.walk(options["whisper_dir"]):
            for filename in files:
                if not filename.endswith(".wsp"):
                    continue

                full_path = os.path.join(root, filename)
                rel_path = os.path.relpath(full_path, options["whisper_dir"])
                parts = rel_path.split(os.sep)
                
                # Check for standard Graphite structure: device/interface/metric.wsp
                # or pointed-at structure: interface/metric.wsp
                if len(parts) == 2:
                    dev_segment = dir_dev_segment
                    if_segment = parts[0]
                    metric = parts[1].replace(".wsp", "")
                elif len(parts) >= 3:
                    dev_segment = parts[-3]
                    if_segment = parts[-2]
                    metric = parts[-1].replace(".wsp", "")
                else:
                    continue

                iface_id = iface_map.get((dev_segment, if_segment))
                
                # Fallback: Try matching shorthand interface names (e.g. gi0-1 -> gigabitethernet0-1)
                if not iface_id:
                    short_if = if_segment.lower().replace("gi", "gigabitethernet").replace("te", "ten-gigabitethernet").replace("xe", "ten-gigabitethernet").replace("et", "ethernet")
                    iface_id = iface_map.get((dev_segment, short_if))

                if iface_id:
                    # Get last timestamp for this specific metric
                    last_ts = checkpoints.get((iface_id, metric), 0)
                    tasks.append((full_path, iface_id, metric, ch_params, last_ts))

                if options['limit'] > 0 and len(tasks) >= options['limit']:
                    break
            if options['limit'] > 0 and len(tasks) >= options['limit']:
                break

        total_files = len(tasks)
        if total_files == 0:
            self.stdout.write(self.style.SUCCESS("No new files or data to migrate."))
            return

        self.stdout.write(f"Starting parallel migration of {total_files} files...")
        processed_files = 0
        total_points = 0
        errors = 0
        start_time = datetime.now()

        with ProcessPoolExecutor(max_workers=options['workers']) as executor:
            future_to_file = {executor.submit(migrate_file, task): task[0] for task in tasks}
            for future in as_completed(future_to_file):
                filename = future_to_file[future]
                try:
                    points, error = future.result()
                    if error:
                        self.stdout.write(self.style.ERROR(f"Error in {filename}: {error}"))
                        errors += 1
                    else:
                        total_points += points
                        processed_files += 1
                        
                    if processed_files % 100 == 0 or processed_files == total_files:
                        elapsed = (datetime.now() - start_time).total_seconds()
                        fps = processed_files / elapsed if elapsed > 0 else 0
                        remaining = (total_files - processed_files) / fps if fps > 0 else 0
                        self.stdout.write(
                            f"Progress: {processed_files}/{total_files} files "
                            f"({(processed_files/total_files)*100:.1f}%) | "
                            f"New Points: {total_points:,} | "
                            f"Speed: {fps:.1f} files/sec | "
                            f"ETA: {remaining/60:.1f} min"
                        )
                except Exception as exc:
                    self.stdout.write(self.style.ERROR(f"{filename} generated an exception: {exc}"))
                    errors += 1

        self.stdout.write(self.style.SUCCESS(f"\nMigration Complete! New Points: {total_points:,}"))
