from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List


def run() -> Dict[str, Any]:
    root = Path(__file__).resolve().parents[3]
    out_dir = root / "model/stgnn/output"
    metrics = out_dir / "metrics.json"
    predictions = out_dir / "predictions.csv"
    report = out_dir / "model_report.md"

    checks: List[Dict[str, Any]] = []

    def add(name: str, ok: bool, detail: str = "") -> None:
        checks.append({"name": name, "ok": bool(ok), "detail": detail})

    add("metrics_exists", metrics.exists(), str(metrics))
    add("predictions_exists", predictions.exists(), str(predictions))
    add("report_exists", report.exists(), str(report))

    payload = json.loads(metrics.read_text(encoding="utf-8")) if metrics.exists() else {}
    model = payload.get("model", {}) if isinstance(payload, dict) else {}
    m = model.get("metrics", {}) if isinstance(model, dict) else {}

    add("model_type", model.get("type") == "stgnn_proxy_ridge", str(model.get("type")))
    add("metric_rmse_positive", float(m.get("rmse", 0)) >= 0, str(m.get("rmse")))
    add("metric_mae_positive", float(m.get("mae", 0)) >= 0, str(m.get("mae")))
    add("metric_mape_positive", float(m.get("mape", 0)) >= 0, str(m.get("mape")))

    passed = sum(1 for x in checks if x["ok"])
    summary = {"pass": passed == len(checks), "total": len(checks), "passed": passed, "failed": len(checks) - passed}
    return {"checks": checks, "summary": summary}


def main() -> int:
    result = run()
    out = Path(__file__).resolve().parents[1] / "output/stgnn_check_result.json"
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result["summary"], ensure_ascii=False))
    print("result_file=model/stgnn/output/stgnn_check_result.json")
    return 0 if result["summary"]["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
