from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List


def run() -> Dict[str, Any]:
    root = Path(__file__).resolve().parents[3]
    ddl = root / "data-pipeline/schema/output/core_schema_ddl.sql"

    checks: List[Dict[str, Any]] = []

    def add(name: str, ok: bool, detail: str = "") -> None:
        checks.append({"name": name, "ok": bool(ok), "detail": detail})

    add("ddl_exists", ddl.exists(), str(ddl))
    text = ddl.read_text(encoding="utf-8") if ddl.exists() else ""

    required_tables = [
        "dim_region",
        "dim_grid",
        "dim_segment",
        "fact_traffic_metric_15m",
        "fact_congestion_event",
        "model_prediction_15m",
        "model_attribution",
    ]
    for table in required_tables:
        add(f"table::{table}", f"CREATE TABLE IF NOT EXISTS {table}" in text, table)

    required_indexes = [
        "idx_fact_metric_window_segment",
        "idx_event_time_segment",
        "idx_prediction_window_segment",
        "idx_attr_prediction",
    ]
    for idx in required_indexes:
        add(f"index::{idx}", idx in text, idx)

    add("partition_window_start", "PARTITION BY RANGE (window_start)" in text, "window partition")
    add("partition_start_ts", "PARTITION BY RANGE (start_ts)" in text, "event partition")

    passed = sum(1 for item in checks if item["ok"])
    summary = {"pass": passed == len(checks), "total": len(checks), "passed": passed, "failed": len(checks) - passed}
    return {"checks": checks, "summary": summary}


def main() -> int:
    result = run()
    out = Path(__file__).resolve().parents[1] / "output/schema_check_result.json"
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result["summary"], ensure_ascii=False))
    print("result_file=data-pipeline/schema/output/schema_check_result.json")
    return 0 if result["summary"]["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
