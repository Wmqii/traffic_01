#!/usr/bin/env python3
"""D1-2 governance runner for anomaly, missing, duplicate, and delay checks."""
import argparse
import csv
import json
from collections import defaultdict
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent.parent
DEFAULT_INPUT_DIR = ROOT_DIR.parent / "ingest" / "staging"
RULES_PATH = ROOT_DIR / "config" / "governance_rules.json"
OUTPUT_DIR = ROOT_DIR / "output"


def parse_iso(ts: str) -> datetime:
    if not ts:
        raise ValueError("empty timestamp")
    normalized = ts.replace("Z", "+00:00")
    return datetime.fromisoformat(normalized)


def parse_number(value: str):
    if value is None or value == "":
        raise ValueError("empty numeric")
    if "." in value:
        return float(value)
    return int(value)


def inject_demo_anomalies(rows_by_source):
    demo = deepcopy(rows_by_source)

    taxi_rows = demo.get("taxi", [])
    if taxi_rows:
        taxi_rows.append(dict(taxi_rows[0]))  # duplicate
        if len(taxi_rows) > 1:
            taxi_rows[1]["passenger_count"] = ""  # missing

    metro_rows = demo.get("metro", [])
    if metro_rows:
        metro_rows[0]["occupancy_pct"] = "180"  # out of range

    weather_rows = demo.get("weather", [])
    if weather_rows:
        weather_rows[0]["timestamp"] = "2026-03-25T00:00:00Z"  # delayed

    event_rows = demo.get("event", [])
    if event_rows:
        event_rows[0]["expected_attendance"] = "-3"  # out of range

    return demo


def load_rows(input_dir: Path):
    rows_by_source = {}
    for path in sorted(input_dir.glob("*.csv")):
        source = path.stem
        with path.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            rows_by_source[source] = [row for row in reader]
    return rows_by_source


def write_csv(path: Path, fieldnames, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def process_source(source, rows, rule, max_delay_minutes):
    clean_rows = []
    reject_rows = []
    metrics = defaultdict(int)
    seen = set()

    if not rows:
        return clean_rows, reject_rows, {
            "source": source,
            "total_rows": 0,
            "clean_rows": 0,
            "reject_rows": 0,
            "anomaly_count": 0,
            "missing_count": 0,
            "duplicate_count": 0,
            "delay_count": 0
        }

    delay_check_enabled = rule.get("delay_check", True)
    latest_ts = None
    if delay_check_enabled:
        latest_ts = max(parse_iso(r.get("timestamp", "")) for r in rows if r.get("timestamp"))

    for row in rows:
        issues = []

        # missing required fields
        for field in rule.get("required_fields", []):
            if row.get(field, "") == "":
                issues.append(f"missing:{field}")
                metrics["missing_count"] += 1

        # duplicate check
        key_fields = rule.get("unique_key", [])
        if key_fields:
            key = tuple(row.get(f, "") for f in key_fields)
            if key in seen:
                issues.append("duplicate:key")
                metrics["duplicate_count"] += 1
            else:
                seen.add(key)

        # range anomalies
        for field, limits in rule.get("numeric_ranges", {}).items():
            try:
                num = parse_number(row.get(field, ""))
                if num < limits["min"] or num > limits["max"]:
                    issues.append(f"anomaly:{field}")
                    metrics["anomaly_count"] += 1
            except ValueError:
                # empty numeric already handled in required/missing if required
                pass

        # delay check (relative to latest record timestamp in source)
        if delay_check_enabled:
            try:
                row_ts = parse_iso(row.get("timestamp", ""))
                delay_minutes = (latest_ts - row_ts).total_seconds() / 60.0
                if delay_minutes > max_delay_minutes:
                    issues.append("delay:late_record")
                    metrics["delay_count"] += 1
            except ValueError:
                issues.append("anomaly:timestamp")
                metrics["anomaly_count"] += 1

        if issues:
            rejected = dict(row)
            rejected["reject_reasons"] = "|".join(issues)
            reject_rows.append(rejected)
        else:
            clean_rows.append(row)

    summary = {
        "source": source,
        "total_rows": len(rows),
        "clean_rows": len(clean_rows),
        "reject_rows": len(reject_rows),
        "anomaly_count": metrics["anomaly_count"],
        "missing_count": metrics["missing_count"],
        "duplicate_count": metrics["duplicate_count"],
        "delay_count": metrics["delay_count"]
    }
    return clean_rows, reject_rows, summary


def run(input_dir: Path, demo: bool):
    with RULES_PATH.open("r", encoding="utf-8") as handle:
        rules = json.load(handle)

    rows_by_source = load_rows(input_dir)
    if demo:
        rows_by_source = inject_demo_anomalies(rows_by_source)

    report_entries = []
    all_sources = sorted(rules["sources"].keys())
    for source in all_sources:
        rows = rows_by_source.get(source, [])
        rule = rules["sources"][source]
        clean_rows, reject_rows, summary = process_source(
            source=source,
            rows=rows,
            rule=rule,
            max_delay_minutes=rules["max_delay_minutes"]
        )

        if rows:
            clean_fields = list(rows[0].keys())
            reject_fields = clean_fields + ["reject_reasons"]
            write_csv(OUTPUT_DIR / "clean" / f"{source}.csv", clean_fields, clean_rows)
            write_csv(OUTPUT_DIR / "rejects" / f"{source}_rejects.csv", reject_fields, reject_rows)

        report_entries.append(summary)

    report = {
        "run_mode": "demo" if demo else "normal",
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "input_dir": str(input_dir),
        "rules_file": str(RULES_PATH),
        "entries": report_entries
    }
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with (OUTPUT_DIR / "governance_report.json").open("w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2, ensure_ascii=True)

    print(f"Governance completed ({report['run_mode']}). Sources processed: {len(report_entries)}.")


def main():
    parser = argparse.ArgumentParser(description="Run D1-2 governance checks.")
    parser.add_argument(
        "--input-dir",
        default=str(DEFAULT_INPUT_DIR),
        help="CSV input directory (default: data-pipeline/ingest/staging)."
    )
    parser.add_argument(
        "--demo-anomalies",
        action="store_true",
        help="Inject synthetic anomalies for rule verification."
    )
    args = parser.parse_args()
    run(Path(args.input_dir), args.demo_anomalies)


if __name__ == "__main__":
    main()
