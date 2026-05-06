from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Tuple
from urllib.error import URLError
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = ROOT / "frontend" / "tests" / "output"
SESSION = "revamp_e2e"
NPX_BIN = "npx.cmd" if os.name == "nt" else "npx"


def wait_http_ready(url: str, timeout: float = 60.0) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with urlopen(url, timeout=3) as resp:  # noqa: S310
                if 200 <= resp.status < 500:
                    return True
        except URLError:
            pass
        time.sleep(0.5)
    return False


def run_cmd(cmd: List[str], timeout: int = 120) -> Tuple[int, str, str]:
    try:
        completed = subprocess.run(  # noqa: S603
            cmd,
            cwd=ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
        )
        return completed.returncode, completed.stdout, completed.stderr
    except FileNotFoundError as exc:
        return 127, "", str(exc)


def run_pw(args: List[str], timeout: int = 120) -> Tuple[int, str, str]:
    cmd = [NPX_BIN, "--yes", "--package", "@playwright/cli", "playwright-cli", "--session", SESSION, *args]
    return run_cmd(cmd, timeout=timeout)


def parse_eval_result(stdout: str) -> str:
    match = re.search(r"### Result\s*\n(.*?)\n### Ran Playwright code", stdout, flags=re.S)
    return match.group(1).strip() if match else ""


def is_pw_success(returncode: int, stdout: str, stderr: str) -> bool:
    if returncode != 0:
        return False
    return "### Error" not in stdout and "### Error" not in stderr


def terminate_process(proc: subprocess.Popen[Any] | None) -> None:
    if not proc:
        return
    if proc.poll() is not None:
        return
    proc.terminate()
    try:
        proc.wait(timeout=10)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait(timeout=5)


def main() -> int:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    checks: List[Dict[str, Any]] = []

    def add(name: str, ok: bool, detail: str = "") -> None:
        checks.append({"name": name, "ok": bool(ok), "detail": detail})

    backend_log = OUTPUT_DIR / "revamp_backend_server.log"
    frontend_log = OUTPUT_DIR / "revamp_frontend_server.log"

    backend_proc: subprocess.Popen[Any] | None = None
    frontend_proc: subprocess.Popen[Any] | None = None

    try:
        env = os.environ.copy()
        env["PYTHONPATH"] = "."

        backend_proc = subprocess.Popen(  # noqa: S603
            [sys.executable, "-m", "uvicorn", "backend.app:app", "--host", "127.0.0.1", "--port", "8000"],
            cwd=ROOT,
            env=env,
            stdout=backend_log.open("w", encoding="utf-8"),
            stderr=subprocess.STDOUT,
            text=True,
        )
        frontend_proc = subprocess.Popen(  # noqa: S603
            [sys.executable, "-m", "http.server", "5500", "--directory", "frontend"],
            cwd=ROOT,
            stdout=frontend_log.open("w", encoding="utf-8"),
            stderr=subprocess.STDOUT,
            text=True,
        )

        add("backend_health_ready", wait_http_ready("http://127.0.0.1:8000/health"), "http://127.0.0.1:8000/health")
        add("frontend_ready", wait_http_ready("http://127.0.0.1:5500/index.html"), "http://127.0.0.1:5500/index.html")

        rc, out, err = run_pw(["open", "http://127.0.0.1:5500/index.html"])
        add("pw_open_page", is_pw_success(rc, out, err), (err or out).strip()[-300:])

        rc, out, err = run_pw(["snapshot"])
        add("pw_snapshot_initial", is_pw_success(rc, out, err), (err or out).strip()[-300:])

        rc, out, err = run_pw(["eval", "() => document.title.includes('交通流量预测')"])
        add("title_contains_keyword", rc == 0 and parse_eval_result(out) == "true", parse_eval_result(out) or err)

        rc, out, err = run_pw(["eval", "() => !document.querySelector('#loginBtn')"])
        add("login_removed", rc == 0 and parse_eval_result(out) == "true", parse_eval_result(out) or err)

        rc, out, err = run_pw(["eval", "() => Array.from(document.querySelectorAll('.tab')).map(x => x.textContent.trim()).join('|')"])
        tab_names = parse_eval_result(out)
        add("tabs_present", rc == 0 and all(x in tab_names for x in ["路况总览", "拥堵归因", "流量预测", "数据说明"]), tab_names)

        rc, out, err = run_pw(["eval", "() => (document.querySelectorAll('#segmentSelect option') || []).length >= 1"])
        add("segment_options_present", rc == 0 and parse_eval_result(out) == "true", parse_eval_result(out) or err)

        switch_tabs_code = (
            "async (page) => {"
            "await page.click('button.tab[data-page=\"attribution\"]');"
            "await page.waitForTimeout(300);"
            "await page.click('button.tab[data-page=\"prediction\"]');"
            "await page.waitForTimeout(300);"
            "await page.click('button.tab[data-page=\"overview\"]');"
            "await page.waitForTimeout(300);"
            "}"
        )
        rc, out, err = run_pw(["run-code", switch_tabs_code], timeout=150)
        add("tab_switch_actions", is_pw_success(rc, out, err), (err or out).strip()[-300:])

        rc, out, err = run_pw(["eval", "() => document.querySelector('#page-overview')?.classList.contains('active')"])
        add("overview_page_active", rc == 0 and parse_eval_result(out) == "true", parse_eval_result(out) or err)

        pick_segment_code = (
            "async (page) => {"
            "const options = await page.locator('#segmentSelect option').all();"
            "if (options.length > 1) {"
            "const value = await options[1].getAttribute('value');"
            "if (value) await page.selectOption('#segmentSelect', value);"
            "}"
            "await page.waitForTimeout(1200);"
            "}"
        )
        rc, out, err = run_pw(["run-code", pick_segment_code], timeout=180)
        add("segment_change_action", is_pw_success(rc, out, err), (err or out).strip()[-300:])

        rc, out, err = run_pw(["eval", "() => (document.querySelector('#selectedSegmentTag')?.textContent || '').trim() !== '未选择'"])
        add("segment_tag_updated", rc == 0 and parse_eval_result(out) == "true", parse_eval_result(out) or err)

        rc, out, err = run_pw(["eval", "() => !!document.querySelector('#segmentFlowChart canvas') || !!document.querySelector('#segmentFlowChart .chart-fallback')"])
        add("overview_chart_or_fallback_present", rc == 0 and parse_eval_result(out) == "true", parse_eval_result(out) or err)

        rc, out, err = run_pw(["run-code", "async (page) => { await page.click('button.tab[data-page=\"prediction\"]'); await page.waitForTimeout(800); }"])
        add("prediction_tab_opened", is_pw_success(rc, out, err), (err or out).strip()[-300:])

        rc, out, err = run_pw(["eval", "() => !!document.querySelector('#predictionMap .leaflet-pane') || !!document.querySelector('#predictionMap .map-fallback')"])
        add("prediction_map_or_fallback_present", rc == 0 and parse_eval_result(out) == "true", parse_eval_result(out) or err)

        rc, out, err = run_pw(["eval", "() => !!document.querySelector('#predMapFrame') && !!document.querySelector('#predMapFrameLabel')"])
        add("prediction_map_timeline_controls_present", rc == 0 and parse_eval_result(out) == "true", parse_eval_result(out) or err)

        rc, out, err = run_pw(["eval", "() => (document.querySelectorAll('#allSegmentPredTable tbody tr') || []).length >= 1"])
        add("all_segment_prediction_table_non_empty", rc == 0 and parse_eval_result(out) == "true", parse_eval_result(out) or err)

        rc, out, err = run_pw(["eval", "() => !!document.querySelector('#modelErrorCompareChart canvas') || !!document.querySelector('#modelErrorCompareChart .chart-fallback')"])
        add("model_error_chart_or_fallback_present", rc == 0 and parse_eval_result(out) == "true", parse_eval_result(out) or err)

        rc, out, err = run_pw(["eval", "() => (document.querySelector('#analysisReport')?.innerText || '').length > 20"])
        add("analysis_report_present", rc == 0 and parse_eval_result(out) == "true", parse_eval_result(out) or err)

    finally:
        run_pw(["close"], timeout=60)
        terminate_process(frontend_proc)
        terminate_process(backend_proc)

    passed = sum(1 for item in checks if item["ok"])
    result = {
        "checks": checks,
        "summary": {
            "pass": passed == len(checks),
            "total": len(checks),
            "passed": passed,
            "failed": len(checks) - passed,
        },
        "artifacts": {
            "backend_log": backend_log.as_posix(),
            "frontend_log": frontend_log.as_posix(),
        },
    }

    output_path = OUTPUT_DIR / "revamp_e2e_result.json"
    output_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result["summary"], ensure_ascii=False))
    print("result_file=frontend/tests/output/revamp_e2e_result.json")
    return 0 if result["summary"]["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
