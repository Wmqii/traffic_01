from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List


def _exists(path: Path) -> bool:
    return path.exists() and path.is_file()


def run() -> Dict[str, Any]:
    root = Path(__file__).resolve().parents[2]
    rel_doc = root / "execution/m5/M5-REL_上线版本与发布说明_v1.0.md"
    manifest = root / "ops/artifacts/m5_release_manifest_v1.json"
    uat_doc = root / "execution/m5/M5-UAT_验收报告_v1.0.md"
    c14_doc = root / "execution/m5/C1-4_验收报告与项目复盘_v1.0.md"

    checks: List[Dict[str, Any]] = []

    def add(name: str, ok: bool, detail: str = "") -> None:
        checks.append({"name": name, "ok": bool(ok), "detail": detail})

    add("rel_doc_exists", _exists(rel_doc), str(rel_doc))
    add("manifest_exists", _exists(manifest), str(manifest))
    add("uat_doc_exists", _exists(uat_doc), str(uat_doc))
    add("c1_4_doc_exists", _exists(c14_doc), str(c14_doc))

    text = rel_doc.read_text(encoding="utf-8") if _exists(rel_doc) else ""
    required_sections = [
        "## 3. 发布版本信息",
        "## 5. 上线前检查清单",
        "## 6. 发布步骤",
        "## 7. 回滚策略",
        "## 8. 发布后观察",
    ]
    for sec in required_sections:
        add(f"section::{sec}", sec in text, sec)

    manifest_ok = False
    if _exists(manifest):
        payload = json.loads(manifest.read_text(encoding="utf-8"))
        rel_ver = str(payload.get("release_version", "")).strip()
        gates = payload.get("release_gates", {})
        gate_ok = bool(gates.get("m4_all_done")) and bool(gates.get("m5_uat_done")) and bool(gates.get("tests_green"))
        components = payload.get("components", [])
        manifest_ok = rel_ver == "traffic-m5-v1.0" and gate_ok and isinstance(components, list) and len(components) >= 4
    add("manifest_content_valid", manifest_ok, "release_version + gates + components")

    passed = sum(1 for item in checks if item["ok"])
    summary = {"pass": passed == len(checks), "total": len(checks), "passed": passed, "failed": len(checks) - passed}
    return {"checks": checks, "summary": summary}


def main() -> int:
    result = run()
    out_dir = Path(__file__).resolve().parent / "output"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / "m5_rel_check_result.json"
    out_file.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result["summary"], ensure_ascii=False))
    print("result_file=execution/m5/output/m5_rel_check_result.json")
    return 0 if result["summary"]["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

