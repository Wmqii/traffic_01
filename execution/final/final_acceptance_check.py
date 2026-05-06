from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any, Dict, List


def _exists(path: Path) -> bool:
    return path.exists() and path.is_file()


def _load_json(path: Path) -> Dict[str, Any]:
    if not _exists(path):
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def run() -> Dict[str, Any]:
    root = Path(__file__).resolve().parents[2]

    required_files = {
        "m2_board": root / "execution/04_M2启动批次任务板.csv",
        "m3_board": root / "execution/05_M3启动批次任务板.csv",
        "m4_close": root / "execution/m4/M4_阶段收口总结_2026-03-27.md",
        "m5_close": root / "execution/m5/M5_阶段收口总结_2026-03-27.md",
        "m5_review_round6": root / "execution/m5/M5_评审记录_2026-03-27_第6轮.md",
        "final_manifest": root / "execution/final/final_delivery_manifest_2026-03-27.md",
        "final_signoff": root / "execution/final/final_signoff_sheet_v1.0.md",
        "m5_board": root / "execution/07_M5启动批次任务板.csv",
        "m5_uat_check": root / "execution/m5/output/m5_uat_check_result.json",
        "m5_rel_check": root / "execution/m5/output/m5_rel_check_result.json",
        "c1_3_check": root / "execution/m5/output/c1_3_doc_check_result.json",
        "c1_4_check": root / "execution/m5/output/c1_4_doc_check_result.json",
        "schema_check": root / "data-pipeline/schema/output/schema_check_result.json",
        "a1_3_check": root / "model/stgnn/output/stgnn_check_result.json",
        "a1_4_check": root / "model/congestion_rules/output/rules_check_result.json",
        "a1_5_check": root / "model/attribution/output/attribution_check_result.json",
    }

    checks: List[Dict[str, Any]] = []

    def add(name: str, ok: bool, detail: str = "") -> None:
        checks.append({"name": name, "ok": bool(ok), "detail": detail})

    for name, path in required_files.items():
        add(f"exists::{name}", _exists(path), str(path.relative_to(root)))

    for board_key in ["m2_board", "m3_board", "m5_board"]:
        board_ok = False
        board_path = required_files[board_key]
        if _exists(board_path):
            with board_path.open("r", encoding="utf-8", newline="") as f:
                rows = list(csv.DictReader(f))
            board_ok = bool(rows) and all(str(r.get("status", "")).strip() == "Done" for r in rows)
        add(f"{board_key}_all_done", board_ok, str(board_path.relative_to(root)))

    for key in [
        "m5_uat_check",
        "m5_rel_check",
        "c1_3_check",
        "c1_4_check",
        "schema_check",
        "a1_3_check",
        "a1_4_check",
        "a1_5_check",
    ]:
        payload = _load_json(required_files[key])
        summary = payload.get("summary", {}) if isinstance(payload, dict) else {}
        add(f"summary_pass::{key}", bool(summary.get("pass") is True), json.dumps(summary, ensure_ascii=False))

    passed = sum(1 for c in checks if c["ok"])
    summary = {
        "pass": passed == len(checks),
        "total": len(checks),
        "passed": passed,
        "failed": len(checks) - passed,
    }

    bundle = {
        "project": "traffic-congestion-analysis-system",
        "date": "2026-03-27",
        "phase": "FINAL",
        "summary": summary,
        "checks": checks,
        "evidence": {
            "m4_close": "execution/m4/M4_阶段收口总结_2026-03-27.md",
            "m5_close": "execution/m5/M5_阶段收口总结_2026-03-27.md",
            "m5_review_round6": "execution/m5/M5_评审记录_2026-03-27_第6轮.md",
            "final_manifest": "execution/final/final_delivery_manifest_2026-03-27.md",
            "final_signoff": "execution/final/final_signoff_sheet_v1.0.md",
            "m2_board": "execution/04_M2启动批次任务板.csv",
            "m3_board": "execution/05_M3启动批次任务板.csv",
            "m5_board": "execution/07_M5启动批次任务板.csv",
            "m5_checks": [
                "execution/m5/output/c1_3_doc_check_result.json",
                "execution/m5/output/c1_4_doc_check_result.json",
                "execution/m5/output/m5_uat_check_result.json",
                "execution/m5/output/m5_rel_check_result.json",
            ],
            "incremental_checks": [
                "data-pipeline/schema/output/schema_check_result.json",
                "model/stgnn/output/stgnn_check_result.json",
                "model/congestion_rules/output/rules_check_result.json",
                "model/attribution/output/attribution_check_result.json",
            ],
        },
    }
    return bundle


def main() -> int:
    result = run()
    out_dir = Path(__file__).resolve().parent / "output"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / "final_acceptance_bundle.json"
    out_file.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result["summary"], ensure_ascii=False))
    print("result_file=execution/final/output/final_acceptance_bundle.json")
    return 0 if result["summary"]["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
