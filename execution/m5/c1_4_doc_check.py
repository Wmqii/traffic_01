from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any, Dict, List


def _file_exists(path: Path) -> bool:
    return path.exists() and path.is_file()


def _has_test_ids(testlog_path: Path, required: List[str]) -> bool:
    if not _file_exists(testlog_path):
        return False
    with testlog_path.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    existing = set()
    for row in rows:
        normalized = {
            str(k).lstrip("\ufeff").strip().strip('"'): ("" if v is None else str(v).strip().strip('"'))
            for k, v in row.items()
        }
        value = str(normalized.get("test_id", "")).strip()
        if value:
            existing.add(value)
    return all(item in existing for item in required)


def run() -> Dict[str, Any]:
    root = Path(__file__).resolve().parents[2]
    main_doc = root / "execution/m5/C1-4_验收报告与项目复盘_v1.0.md"
    testlog = root / "execution/logs/testlog.csv"
    worklog = root / "execution/logs/worklog.csv"
    releaselog = root / "execution/logs/releaselog.csv"

    checks: List[Dict[str, Any]] = []

    def add(name: str, ok: bool, detail: str = "") -> None:
        checks.append({"name": name, "ok": bool(ok), "detail": detail})

    add("main_doc_exists", _file_exists(main_doc), str(main_doc))
    add("testlog_exists", _file_exists(testlog), str(testlog))
    add("worklog_exists", _file_exists(worklog), str(worklog))
    add("releaselog_exists", _file_exists(releaselog), str(releaselog))

    text = main_doc.read_text(encoding="utf-8") if _file_exists(main_doc) else ""
    required_sections = [
        "## 3. 验收结果总览",
        "## 4. UAT 就绪性结论",
        "## 5. 项目复盘",
        "### 5.1 做得好的点",
        "### 5.4 改进行动（下一迭代）",
    ]
    for sec in required_sections:
        add(f"section::{sec}", sec in text, sec)

    required_test_ids = ["TL-0038", "TL-0040", "TL-0041", "TL-0046", "TL-0049"]
    add("required_test_ids_present", _has_test_ids(testlog, required_test_ids), ",".join(required_test_ids))

    required_refs = [
        root / "execution/m5/C1-3_用户手册与运维手册_v1.0.md",
        root / "execution/m5/C1-3_验证记录_2026-03-27.md",
        root / "execution/m4/M4_阶段收口总结_2026-03-27.md",
        root / "execution/m5/M5_入口检查与启动说明_v1.0.md",
    ]
    for ref in required_refs:
        add(f"ref::{ref.name}", _file_exists(ref), str(ref))

    passed = sum(1 for item in checks if item["ok"])
    summary = {"pass": passed == len(checks), "total": len(checks), "passed": passed, "failed": len(checks) - passed}
    return {"checks": checks, "summary": summary}


def main() -> int:
    result = run()
    out_dir = Path(__file__).resolve().parent / "output"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / "c1_4_doc_check_result.json"
    out_file.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result["summary"], ensure_ascii=False))
    print("result_file=execution/m5/output/c1_4_doc_check_result.json")
    return 0 if result["summary"]["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
