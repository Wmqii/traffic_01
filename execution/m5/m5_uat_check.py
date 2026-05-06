from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any, Dict, List


def _exists(path: Path) -> bool:
    return path.exists() and path.is_file()


def _csv_has_ids(path: Path, key_name: str, ids: List[str]) -> bool:
    if not _exists(path):
        return False
    with path.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    existing = set()
    for row in rows:
        normalized = {
            str(k).lstrip("\ufeff").strip().strip('"'): ("" if v is None else str(v).strip().strip('"'))
            for k, v in row.items()
        }
        value = normalized.get(key_name, "")
        if value:
            existing.add(value)
    return all(item in existing for item in ids)


def run() -> Dict[str, Any]:
    root = Path(__file__).resolve().parents[2]
    doc = root / "execution/m5/M5-UAT_验收报告_v1.0.md"
    testlog = root / "execution/logs/testlog.csv"
    releaselog = root / "execution/logs/releaselog.csv"

    checks: List[Dict[str, Any]] = []

    def add(name: str, ok: bool, detail: str = "") -> None:
        checks.append({"name": name, "ok": bool(ok), "detail": detail})

    add("uat_doc_exists", _exists(doc), str(doc))
    add("testlog_exists", _exists(testlog), str(testlog))
    add("releaselog_exists", _exists(releaselog), str(releaselog))

    text = doc.read_text(encoding="utf-8") if _exists(doc) else ""
    required_sections = [
        "## 2. UAT 范围",
        "## 3. 验收场景与结果",
        "## 4. 缺陷与风险",
        "## 5. 签字流转",
        "## 6. 后续动作",
    ]
    for sec in required_sections:
        add(f"section::{sec}", sec in text, sec)

    required_test_ids = ["TL-0038", "TL-0040", "TL-0041", "TL-0046", "TL-0050"]
    add("required_uat_test_ids", _csv_has_ids(testlog, "test_id", required_test_ids), ",".join(required_test_ids))

    required_release_ids = ["RL-0034", "RL-0035", "RL-0036"]
    add("required_release_ids", _csv_has_ids(releaselog, "release_id", required_release_ids), ",".join(required_release_ids))

    passed = sum(1 for item in checks if item["ok"])
    summary = {"pass": passed == len(checks), "total": len(checks), "passed": passed, "failed": len(checks) - passed}
    return {"checks": checks, "summary": summary}


def main() -> int:
    result = run()
    out_dir = Path(__file__).resolve().parent / "output"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / "m5_uat_check_result.json"
    out_file.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result["summary"], ensure_ascii=False))
    print("result_file=execution/m5/output/m5_uat_check_result.json")
    return 0 if result["summary"]["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

