from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Tuple


ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = ROOT / "execution" / "m4" / "output"


def run_step(step_id: str, command: List[str], timeout: int) -> Dict[str, Any]:
    started = time.time()
    proc = subprocess.run(  # noqa: S603
        command,
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
    )
    elapsed = round(time.time() - started, 2)
    return {
        "step_id": step_id,
        "command": " ".join(command),
        "returncode": proc.returncode,
        "duration_sec": elapsed,
        "ok": proc.returncode == 0,
        "stdout_tail": (proc.stdout or "")[-1200:],
        "stderr_tail": (proc.stderr or "")[-1200:],
    }


def main() -> int:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    py = sys.executable

    steps: List[Tuple[str, List[str], int]] = [
        ("T1-2_api_automation", [py, "backend/tests/api_automation_runner.py"], 180),
        ("T1-3_frontend_e2e", [py, "frontend/tests/t1_3_e2e_runner.py"], 420),
        ("T1-4_performance_baseline", [py, "backend/tests/performance_runner.py"], 240),
    ]

    results: List[Dict[str, Any]] = []
    for step_id, cmd, timeout in steps:
        results.append(run_step(step_id, cmd, timeout))

    passed = sum(1 for item in results if item["ok"])
    summary = {
        "pass": passed == len(results),
        "total": len(results),
        "passed": passed,
        "failed": len(results) - passed,
    }

    output = {
        "meta": {
            "task_id": "T1-5",
            "stage": "M4",
            "run_mode": "quality_gate_aggregate",
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        },
        "steps": results,
        "summary": summary,
        "evidence": {
            "t1_2_result": "backend/tests/output/t1_2_api_test_result.json",
            "t1_3_result": "frontend/tests/output/t1_3_e2e_result.json",
            "t1_4_result": "backend/tests/output/t1_4_perf_result.json",
        },
    }

    out_file = OUTPUT_DIR / "t1_5_quality_gate_result.json"
    out_file.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")

    print(json.dumps(summary, ensure_ascii=False))
    print("result_file=execution/m4/output/t1_5_quality_gate_result.json")
    return 0 if summary["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

