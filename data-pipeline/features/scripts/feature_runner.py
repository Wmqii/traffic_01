#!/usr/bin/env python3
"""D1-4 feature engineering runner."""
import csv
import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo


ROOT_DIR = Path(__file__).resolve().parent.parent
INPUT_PATH = ROOT_DIR.parent / "alignment" / "output" / "aligned" / "aligned_records.csv"
SPEC_PATH = ROOT_DIR / "config" / "feature_spec.json"
OUTPUT_DIR = ROOT_DIR / "output"
FEATURE_PATH = OUTPUT_DIR / "feature_table.csv"
REPORT_PATH = OUTPUT_DIR / "feature_report.json"


def parse_iso(ts: str) -> datetime:
    return datetime.fromisoformat(ts.replace("Z", "+00:00"))


def to_float(value: str) -> float:
    if value is None or value == "":
        return 0.0
    return float(value)


def read_rows(path: Path):
    with path.open("r", encoding="utf-8", newline="") as handle:
        return [row for row in csv.DictReader(handle)]


def aggregate_rows(rows):
    # key: (source, segment_id, grid_id, window_start, window_end, metric_name)
    grouped = defaultdict(list)
    for row in rows:
        key = (
            row["source"],
            row["segment_id"],
            row["grid_id"],
            row["window_start"],
            row["window_end"],
            row["metric_name"]
        )
        grouped[key].append(to_float(row["metric_value"]))
    return grouped


def build_external_maps(rows, event_metric_name, weather_metric_name):
    event_by_window = defaultdict(float)
    weather_by_window = defaultdict(list)
    for row in rows:
        window = row["window_start"]
        val = to_float(row["metric_value"])
        if row["metric_name"] == event_metric_name:
            event_by_window[window] += val
        if row["metric_name"] == weather_metric_name:
            weather_by_window[window].append(val)
    weather_avg_by_window = {}
    for win, values in weather_by_window.items():
        weather_avg_by_window[win] = sum(values) / len(values) if values else 0.0
    return event_by_window, weather_avg_by_window


def main():
    with SPEC_PATH.open("r", encoding="utf-8") as handle:
        spec = json.load(handle)

    tz = ZoneInfo(spec["timezone"])
    peak_hours = set(spec["peak_hours"])
    lag_steps = spec["lag_steps"]
    event_metric_name = spec["external_features"]["event_metric_name"]
    weather_metric_name = spec["external_features"]["weather_metric_name"]

    rows = read_rows(INPUT_PATH)
    grouped = aggregate_rows(rows)
    event_by_window, weather_avg_by_window = build_external_maps(rows, event_metric_name, weather_metric_name)

    # build base feature rows
    features = []
    for key, values in grouped.items():
        source, segment_id, grid_id, window_start, window_end, metric_name = key
        ws = parse_iso(window_start).astimezone(tz)
        metric_sum = sum(values)
        metric_count = len(values)
        metric_avg = metric_sum / metric_count if metric_count else 0.0
        metric_max = max(values) if values else 0.0

        segment_num = "".join(ch for ch in segment_id if ch.isdigit())
        grid_prefix = grid_id.split("-")[1][0] if "-" in grid_id and len(grid_id.split("-")[1]) > 0 else ""

        features.append({
            "source": source,
            "segment_id": segment_id,
            "grid_id": grid_id,
            "window_start": window_start,
            "window_end": window_end,
            "metric_name": metric_name,
            "metric_sum": round(metric_sum, 4),
            "metric_avg": round(metric_avg, 4),
            "metric_max": round(metric_max, 4),
            "metric_count": metric_count,
            "hour_of_day": ws.hour,
            "day_of_week": ws.weekday(),
            "is_weekend": 1 if ws.weekday() >= 5 else 0,
            "is_peak_hour": 1 if ws.hour in peak_hours else 0,
            "segment_numeric": int(segment_num) if segment_num else 0,
            "grid_area": grid_prefix,
            "event_attendance_window_sum": round(event_by_window.get(window_start, 0.0), 4),
            "weather_precip_window_avg": round(weather_avg_by_window.get(window_start, 0.0), 4)
        })

    # sort for deterministic lag features
    features.sort(key=lambda x: (x["source"], x["segment_id"], x["window_start"]))

    # add lag features
    by_series = defaultdict(list)
    for idx, row in enumerate(features):
        series_key = (row["source"], row["segment_id"], row["metric_name"])
        by_series[series_key].append(idx)

    for indexes in by_series.values():
        for pos, idx in enumerate(indexes):
            for lag in lag_steps:
                col = f"lag{lag}_metric_sum"
                if pos - lag >= 0:
                    prev_idx = indexes[pos - lag]
                    features[idx][col] = features[prev_idx]["metric_sum"]
                else:
                    features[idx][col] = ""

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "source", "segment_id", "grid_id", "window_start", "window_end", "metric_name",
        "metric_sum", "metric_avg", "metric_max", "metric_count",
        "hour_of_day", "day_of_week", "is_weekend", "is_peak_hour",
        "segment_numeric", "grid_area",
        "event_attendance_window_sum", "weather_precip_window_avg",
    ] + [f"lag{lag}_metric_sum" for lag in lag_steps]

    with FEATURE_PATH.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(features)

    report = {
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "input_file": str(INPUT_PATH),
        "spec_file": str(SPEC_PATH),
        "output_file": str(FEATURE_PATH),
        "total_features_rows": len(features),
        "feature_columns": fieldnames,
        "sources": sorted({r["source"] for r in features})
    }
    with REPORT_PATH.open("w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2, ensure_ascii=True)

    print(f"Feature engineering completed. Rows: {len(features)}")


if __name__ == "__main__":
    main()

