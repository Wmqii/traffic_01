#!/usr/bin/env python3
"""D1-3 map matching + time alignment runner."""
import csv
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent.parent
INPUT_DIR = ROOT_DIR.parent / "governance" / "output" / "clean"
MAPPING_PATH = ROOT_DIR / "config" / "spatial_mapping.json"
OUTPUT_DIR = ROOT_DIR / "output"
ALIGNED_PATH = OUTPUT_DIR / "aligned" / "aligned_records.csv"
REPORT_PATH = OUTPUT_DIR / "alignment_report.json"


METRIC_FIELDS = {
    "taxi": ("passenger_count", "passenger_count"),
    "metro": ("occupancy_pct", "occupancy_pct"),
    "weather": ("precip_mm", "precip_mm"),
    "event": ("expected_attendance", "expected_attendance")
}

ENTITY_FIELDS = {
    "taxi": "ride_id",
    "metro": "train_id",
    "weather": "station_id",
    "event": "event_id"
}


def parse_iso(ts: str) -> datetime:
    return datetime.fromisoformat(ts.replace("Z", "+00:00"))


def floor_15m(ts: datetime) -> datetime:
    minute = (ts.minute // 15) * 15
    return ts.replace(minute=minute, second=0, microsecond=0)


def load_csv(path: Path):
    with path.open("r", encoding="utf-8", newline="") as handle:
        return [row for row in csv.DictReader(handle)]


def run():
    with MAPPING_PATH.open("r", encoding="utf-8") as handle:
        mapping = json.load(handle)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUTPUT_DIR / "aligned").mkdir(parents=True, exist_ok=True)

    aligned_rows = []
    summary = []

    for source in sorted(METRIC_FIELDS.keys()):
        source_file = INPUT_DIR / f"{source}.csv"
        if not source_file.exists():
            summary.append({
                "source": source,
                "input_rows": 0,
                "aligned_rows": 0,
                "unmapped_rows": 0
            })
            continue

        rows = load_csv(source_file)
        source_mapping = mapping[source]
        zone_field = source_mapping["zone_field"]
        metric_field, metric_name = METRIC_FIELDS[source]
        entity_field = ENTITY_FIELDS[source]

        aligned_count = 0
        unmapped_count = 0

        for row in rows:
            zone = row.get(zone_field, "")
            segment_id = source_mapping["segment_map"].get(zone, "")
            grid_id = source_mapping["grid_map"].get(zone, "")
            if not segment_id or not grid_id:
                unmapped_count += 1
                continue

            ts = parse_iso(row["timestamp"])
            w_start = floor_15m(ts)
            w_end = w_start + timedelta(minutes=15)

            aligned_rows.append({
                "source": source,
                "entity_id": row.get(entity_field, ""),
                "timestamp": row["timestamp"],
                "window_start": w_start.isoformat(),
                "window_end": w_end.isoformat(),
                "segment_id": segment_id,
                "grid_id": grid_id,
                "metric_name": metric_name,
                "metric_value": row.get(metric_field, "")
            })
            aligned_count += 1

        summary.append({
            "source": source,
            "input_rows": len(rows),
            "aligned_rows": aligned_count,
            "unmapped_rows": unmapped_count
        })

    fieldnames = [
        "source", "entity_id", "timestamp", "window_start", "window_end",
        "segment_id", "grid_id", "metric_name", "metric_value"
    ]
    with ALIGNED_PATH.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(aligned_rows)

    report = {
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "input_dir": str(INPUT_DIR),
        "mapping_file": str(MAPPING_PATH),
        "aligned_file": str(ALIGNED_PATH),
        "total_aligned_rows": len(aligned_rows),
        "summary": summary
    }
    with REPORT_PATH.open("w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2, ensure_ascii=True)

    print(f"Alignment completed. Total aligned rows: {len(aligned_rows)}")


if __name__ == "__main__":
    run()

