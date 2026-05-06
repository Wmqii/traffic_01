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
SESSION = "t1_3_e2e"
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

    backend_log = OUTPUT_DIR / "t1_3_backend_server.log"
    frontend_log = OUTPUT_DIR / "t1_3_frontend_server.log"

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

        login_code = (
            "async (page) => { "
            "await page.fill('#apiBase', 'http://127.0.0.1:8000'); "
            "await page.fill('#username', 'viewer'); "
            "await page.fill('#password', 'viewer123'); "
            "await page.click('#loginBtn'); "
            "await page.waitForTimeout(2500); "
            "}"
        )
        rc, out, err = run_pw(["run-code", login_code], timeout=150)
        add("login_action_executed", is_pw_success(rc, out, err), (err or out).strip()[-300:])

        rc, out, err = run_pw(
            ["eval", "() => /已登录|接口拉取成功|部分接口/.test(document.querySelector('#authStatus')?.textContent || '')"]
        )
        add("auth_status_after_login_valid", rc == 0 and parse_eval_result(out) == "true", parse_eval_result(out) or err)

        rc, out, err = run_pw(["eval", "() => (document.querySelectorAll('#segmentSelect option') || []).length >= 1"])
        add(
            "segment_options_present_after_login",
            rc == 0 and parse_eval_result(out) == "true",
            parse_eval_result(out) or err,
        )

        nav_and_linkage_code = (
            "async (page) => { "
            "await page.click('button.tab[data-page=\"realtime\"]'); "
            "await page.waitForTimeout(400); "
            "const segmentOption = await page.locator('#segmentSelect option').nth(1).getAttribute('value'); "
            "if (segmentOption) { await page.selectOption('#segmentSelect', segmentOption); } "
            "await page.waitForTimeout(1200); "
            "const firstRow = page.locator('#eventsTable tbody tr').first(); "
            "if (await firstRow.count()) { await firstRow.click(); } "
            "await page.waitForTimeout(1200); "
            "}"
        )
        rc, out, err = run_pw(["run-code", nav_and_linkage_code], timeout=180)
        add("realtime_nav_and_linkage_action", is_pw_success(rc, out, err), (err or out).strip()[-300:])

        rc, out, err = run_pw(["eval", "() => document.querySelector('#page-realtime')?.classList.contains('active')"])
        add("realtime_page_active", rc == 0 and parse_eval_result(out) == "true", parse_eval_result(out) or err)

        rc, out, err = run_pw(
            ["eval", "() => (document.querySelector('#selectedEventTag')?.textContent || '').trim() !== '未选择'"]
        )
        add("event_tag_selected", rc == 0 and parse_eval_result(out) == "true", parse_eval_result(out) or err)

        rc, before_out, err = run_pw(["eval", "() => document.querySelector('#heatFrameLabel')?.textContent || ''"])
        before_frame = parse_eval_result(before_out)
        add("heat_frame_label_readable_before", rc == 0 and bool(before_frame), before_frame or err)

        replay_code = (
            "async (page) => { "
            "await page.click('#heatPlayBtn'); "
            "await page.waitForTimeout(1800); "
            "await page.click('#heatPauseBtn'); "
            "}"
        )
        rc, out, err = run_pw(["run-code", replay_code], timeout=150)
        add("heat_replay_play_pause_action", is_pw_success(rc, out, err), (err or out).strip()[-300:])

        rc, after_out, err = run_pw(["eval", "() => document.querySelector('#heatFrameLabel')?.textContent || ''"])
        after_frame = parse_eval_result(after_out)
        add(
            "heat_frame_label_changed_after_play",
            rc == 0 and bool(after_frame) and after_frame != before_frame,
            f"before={before_frame}; after={after_frame}",
        )

        export_code = (
            "async (page) => { "
            "await page.click('button.tab[data-page=\"management\"]'); "
            "await page.waitForTimeout(500); "
            "for (const selector of ['#exportChartBtn', '#exportEventsCsvBtn', '#exportBriefBtn']) { "
            "const [download] = await Promise.all([page.waitForEvent('download'), page.click(selector)]); "
            "await download.delete(); "
            "} "
            "await page.waitForTimeout(500); "
            "}"
        )
        rc, out, err = run_pw(["run-code", export_code], timeout=240)
        add("management_export_downloads", is_pw_success(rc, out, err), (err or out).strip()[-300:])

        rc, out, err = run_pw(["eval", "() => document.querySelector('#runtimeLog')?.innerText.includes('已导出')"])
        add("runtime_log_exported", rc == 0 and parse_eval_result(out) == "true", parse_eval_result(out) or err)

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

    output_path = OUTPUT_DIR / "t1_3_e2e_result.json"
    output_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result["summary"], ensure_ascii=False))
    print("result_file=frontend/tests/output/t1_3_e2e_result.json")
    return 0 if result["summary"]["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
