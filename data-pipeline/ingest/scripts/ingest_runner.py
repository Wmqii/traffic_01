#!/usr/bin/env python3
"""Minimal ingest runner that copies sample CSVs into staging."""
import csv
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
SAMPLES_DIR = ROOT_DIR / "samples"
STAGING_DIR = ROOT_DIR / "staging"
REPORT_PATH = STAGING_DIR / "ingest_report.json"


def _read_sample_summary(sample_path: Path):
    with sample_path.open("r", newline="", encoding="utf-8") as handle:
        reader = [row for row in csv.reader(handle)]

    header = reader[0] if reader else []
    data_rows = max(0, len(reader) - 1)
    return header, data_rows


def run():
    STAGING_DIR.mkdir(parents=True, exist_ok=True)
    sample_files = sorted(SAMPLES_DIR.glob("*.csv"))
    if not sample_files:
        raise SystemExit("No sample CSV files found under samples/.")

    started_at = datetime.now(timezone.utc)
    entries = []

    for sample_path in sample_files:
        destination = STAGING_DIR / sample_path.name
        shutil.copy2(sample_path, destination)
        header, row_count = _read_sample_summary(sample_path)
        entries.append({
            "source": str(sample_path.relative_to(ROOT_DIR)),
            "target": str(destination.relative_to(ROOT_DIR)),
            "header": header,
            "row_count": row_count,
            "copied_at": datetime.now(timezone.utc).isoformat(),
        })

    report = {
        "run_started_at": started_at.isoformat(),
        "run_completed_at": datetime.now(timezone.utc).isoformat(),
        "total_samples": len(entries),
        "entries": entries,
    }

    with REPORT_PATH.open("w", encoding="utf-8") as report_file:
        json.dump(report, report_file, indent=2, ensure_ascii=True)

    print(f"Copied {len(entries)} sample files to {STAGING_DIR.name} and wrote {REPORT_PATH.name}.")


if __name__ == "__main__":
    run()
