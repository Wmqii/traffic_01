from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List


def run() -> Dict[str, Any]:
    root = Path(__file__).resolve().parents[3]
    out = root / "model/congestion_rules/output"
    cfg = out / "calibration_config.json"
    eva = out / "rule_evaluation.json"
    pred = out / "rule_predictions.csv"
    report = out / "rule_report.md"

    checks: List[Dict[str, Any]] = []

    def add(name: str, ok: bool, detail: str = "") -> None:
        checks.append({"name": name, "ok": bool(ok), "detail": detail})

    add("config_exists", cfg.exists(), str(cfg))
    add("evaluation_exists", eva.exists(), str(eva))
    add("predictions_exists", pred.exists(), str(pred))
    add("report_exists", report.exists(), str(report))

    payload = json.loads(eva.read_text(encoding="utf-8")) if eva.exists() else {}
    overall = payload.get("overall", {}) if isinstance(payload, dict) else {}
    add("overall_f1_non_negative", float(overall.get("f1", 0)) >= 0, str(overall.get("f1")))
    add("overall_precision_non_negative", float(overall.get("precision", 0)) >= 0, str(overall.get("precision")))
    add("overall_recall_non_negative", float(overall.get("recall", 0)) >= 0, str(overall.get("recall")))

    passed = sum(1 for c in checks if c["ok"])
    summary = {"pass": passed == len(checks), "total": len(checks), "passed": passed, "failed": len(checks) - passed}
    return {"checks": checks, "summary": summary}


def main() -> int:
    result = run()
    out = Path(__file__).resolve().parents[1] / "output/rules_check_result.json"
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result["summary"], ensure_ascii=False))
    print("result_file=model/congestion_rules/output/rules_check_result.json")
    return 0 if result["summary"]["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
