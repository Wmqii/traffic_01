from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List


def run() -> Dict[str, Any]:
    root = Path(__file__).resolve().parents[3]
    out = root / "model/attribution/output"
    summary = out / "attribution_summary.json"
    shap_like = out / "shap_like_values.csv"
    card = out / "model_card.md"

    checks: List[Dict[str, Any]] = []

    def add(name: str, ok: bool, detail: str = "") -> None:
        checks.append({"name": name, "ok": bool(ok), "detail": detail})

    add("summary_exists", summary.exists(), str(summary))
    add("shap_like_exists", shap_like.exists(), str(shap_like))
    add("card_exists", card.exists(), str(card))

    payload = json.loads(summary.read_text(encoding="utf-8")) if summary.exists() else {}
    top = payload.get("global_top_features", []) if isinstance(payload, dict) else []
    samples = payload.get("sample_explanations", []) if isinstance(payload, dict) else []
    add("global_top_non_empty", isinstance(top, list) and len(top) >= 3, str(len(top)))
    add("sample_explanations_non_empty", isinstance(samples, list) and len(samples) >= 1, str(len(samples)))

    passed = sum(1 for c in checks if c["ok"])
    summary_payload = {"pass": passed == len(checks), "total": len(checks), "passed": passed, "failed": len(checks) - passed}
    return {"checks": checks, "summary": summary_payload}


def main() -> int:
    result = run()
    out = Path(__file__).resolve().parents[1] / "output/attribution_check_result.json"
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result["summary"], ensure_ascii=False))
    print("result_file=model/attribution/output/attribution_check_result.json")
    return 0 if result["summary"]["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
