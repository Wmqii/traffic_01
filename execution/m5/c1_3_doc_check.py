from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List


def _exists(path: Path) -> bool:
    return path.exists() and path.is_file()


def run() -> Dict[str, Any]:
    root = Path(__file__).resolve().parents[2]
    main_doc = root / "execution/m5/C1-3_用户手册与运维手册_v1.0.md"
    training_doc = root / "execution/m5/C1-3_培训材料提纲_v1.0.md"

    checks: List[Dict[str, Any]] = []

    def add(name: str, ok: bool, detail: str = "") -> None:
        checks.append({"name": name, "ok": bool(ok), "detail": detail})

    add("main_doc_exists", _exists(main_doc), str(main_doc))
    add("training_doc_exists", _exists(training_doc), str(training_doc))

    text = main_doc.read_text(encoding="utf-8") if _exists(main_doc) else ""
    required_sections = [
        "## 3. 用户手册",
        "### 3.1 登录与权限",
        "### 3.3 核心业务流程",
        "## 4. 运维手册",
        "### 4.2 标准操作流程",
        "### 4.3 发布与回滚",
        "### 4.4 审计与错误处理",
        "## 5. 验收映射",
    ]
    for section in required_sections:
        add(f"section::{section}", section in text, section)

    required_refs = [
        root / "frontend/README.md",
        root / "backend/README.md",
        root / "ops/README.md",
        root / "execution/m4/O1-5_运行手册与应急预案实施说明_v1.0.md",
        root / "execution/m4/B1-5_审计日志与错误码规范实施说明_v1.0.md",
    ]
    for ref in required_refs:
        add(f"ref::{ref.name}", _exists(ref), str(ref))

    passed = sum(1 for item in checks if item["ok"])
    summary = {
        "pass": passed == len(checks),
        "total": len(checks),
        "passed": passed,
        "failed": len(checks) - passed,
    }
    return {"checks": checks, "summary": summary}


def main() -> int:
    result = run()
    out_dir = Path(__file__).resolve().parent / "output"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / "c1_3_doc_check_result.json"
    out_file.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result["summary"], ensure_ascii=False))
    print("result_file=execution/m5/output/c1_3_doc_check_result.json")
    return 0 if result["summary"]["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
