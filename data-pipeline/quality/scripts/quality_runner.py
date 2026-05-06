#!/usr/bin/env python3
"""D1-5 quality monitoring and scoring runner."""
import csv
import json
from datetime import datetime, timezone
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent.parent
RULES_PATH = ROOT_DIR / "config" / "quality_rules.json"
INGEST_REPORT = ROOT_DIR.parent / "ingest" / "staging" / "ingest_report.json"
GOVERNANCE_REPORT = ROOT_DIR.parent / "governance" / "output" / "governance_report_normal.json"
ALIGNMENT_REPORT = ROOT_DIR.parent / "alignment" / "output" / "alignment_report.json"
FEATURE_TABLE = ROOT_DIR.parent / "features" / "output" / "feature_table.csv"
OUTPUT_DIR = ROOT_DIR / "output"
SCOREBOARD_CSV = OUTPUT_DIR / "quality_scoreboard.csv"
QUALITY_REPORT = OUTPUT_DIR / "quality_report.json"
ECHARTS_OPTION = OUTPUT_DIR / "quality_dashboard_echarts.json"


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def clamp_score(value: float) -> float:
    return max(0.0, min(100.0, round(value, 2)))


def grade_of(score: float, grading_rules):
    for rule in grading_rules:
        if score >= rule["min"]:
            return rule["grade"]
    return "D"


def safe_ratio(numerator: float, denominator: float) -> float:
    if denominator <= 0:
        return 100.0
    return (numerator / denominator) * 100.0


def count_feature_rows_by_source(path: Path):
    counts = {}
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            source = row["source"]
            counts[source] = counts.get(source, 0) + 1
    return counts


def build_echarts_option(rows):
    sources = [r["source"] for r in rows]
    overall = [r["overall_score"] for r in rows]
    completeness = [r["completeness_score"] for r in rows]
    validity = [r["validity_score"] for r in rows]
    timeliness = [r["timeliness_score"] for r in rows]

    return {
        "title": {"text": "Data Quality Scoreboard"},
        "tooltip": {"trigger": "axis"},
        "legend": {"data": ["Overall", "Completeness", "Validity", "Timeliness"]},
        "xAxis": {"type": "category", "data": sources},
        "yAxis": {"type": "value", "min": 0, "max": 100},
        "series": [
            {"name": "Overall", "type": "bar", "data": overall},
            {"name": "Completeness", "type": "line", "data": completeness},
            {"name": "Validity", "type": "line", "data": validity},
            {"name": "Timeliness", "type": "line", "data": timeliness}
        ]
    }


def run():
    rules = load_json(RULES_PATH)
    governance = load_json(GOVERNANCE_REPORT)
    alignment = load_json(ALIGNMENT_REPORT)
    ingest = load_json(INGEST_REPORT)
    feature_counts = count_feature_rows_by_source(FEATURE_TABLE)

    weights = rules["weights"]
    grading_rules = rules["grading"]
    pass_threshold = rules["pass_threshold"]

    align_by_source = {x["source"]: x for x in alignment["summary"]}
    rows = []
    for entry in governance["entries"]:
        source = entry["source"]
        total_rows = entry["total_rows"]
        clean_rows = entry["clean_rows"]
        reject_rows = entry["reject_rows"]
        missing_count = entry["missing_count"]
        duplicate_count = entry["duplicate_count"]
        anomaly_count = entry["anomaly_count"]
        delay_count = entry["delay_count"]

        aligned_rows = align_by_source.get(source, {}).get("aligned_rows", 0)
        feature_rows = feature_counts.get(source, 0)

        completeness_score = clamp_score(safe_ratio(total_rows - missing_count, total_rows))
        validity_score = clamp_score(safe_ratio(total_rows - anomaly_count, total_rows))
        uniqueness_score = clamp_score(safe_ratio(total_rows - duplicate_count, total_rows))
        timeliness_score = clamp_score(safe_ratio(total_rows - delay_count, total_rows))

        alignment_score = clamp_score(safe_ratio(aligned_rows, clean_rows))
        feature_coverage_score = clamp_score(safe_ratio(feature_rows, aligned_rows))
        pipeline_consistency_score = round((alignment_score + feature_coverage_score) / 2.0, 2)

        overall = (
            completeness_score * weights["completeness"]
            + validity_score * weights["validity"]
            + uniqueness_score * weights["uniqueness"]
            + timeliness_score * weights["timeliness"]
            + pipeline_consistency_score * weights["pipeline_consistency"]
        )
        overall = clamp_score(overall)
        status = "PASS" if overall >= pass_threshold else "WARN"

        rows.append({
            "source": source,
            "total_rows": total_rows,
            "clean_rows": clean_rows,
            "reject_rows": reject_rows,
            "missing_count": missing_count,
            "duplicate_count": duplicate_count,
            "anomaly_count": anomaly_count,
            "delay_count": delay_count,
            "aligned_rows": aligned_rows,
            "feature_rows": feature_rows,
            "completeness_score": completeness_score,
            "validity_score": validity_score,
            "uniqueness_score": uniqueness_score,
            "timeliness_score": timeliness_score,
            "alignment_score": alignment_score,
            "feature_coverage_score": feature_coverage_score,
            "pipeline_consistency_score": pipeline_consistency_score,
            "overall_score": overall,
            "grade": grade_of(overall, grading_rules),
            "status": status
        })

    rows.sort(key=lambda x: x["source"])
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "source", "total_rows", "clean_rows", "reject_rows",
        "missing_count", "duplicate_count", "anomaly_count", "delay_count",
        "aligned_rows", "feature_rows",
        "completeness_score", "validity_score", "uniqueness_score", "timeliness_score",
        "alignment_score", "feature_coverage_score", "pipeline_consistency_score",
        "overall_score", "grade", "status"
    ]

    with SCOREBOARD_CSV.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    avg_score = round(sum(r["overall_score"] for r in rows) / len(rows), 2) if rows else 0.0
    pass_count = sum(1 for r in rows if r["status"] == "PASS")
    report = {
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "rules_file": str(RULES_PATH),
        "source_reports": {
            "ingest": str(INGEST_REPORT),
            "governance": str(GOVERNANCE_REPORT),
            "alignment": str(ALIGNMENT_REPORT),
            "feature_table": str(FEATURE_TABLE)
        },
        "ingest_total_samples": ingest.get("total_samples", 0),
        "sources": rows,
        "summary": {
            "source_count": len(rows),
            "pass_count": pass_count,
            "avg_overall_score": avg_score
        }
    }

    with QUALITY_REPORT.open("w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2, ensure_ascii=True)

    option = build_echarts_option(rows)
    with ECHARTS_OPTION.open("w", encoding="utf-8") as handle:
        json.dump(option, handle, indent=2, ensure_ascii=True)

    print(f"Quality scoring completed. Sources: {len(rows)}, pass: {pass_count}, avg_score: {avg_score}")


if __name__ == "__main__":
    run()

