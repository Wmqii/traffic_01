from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Dict, List

from fastapi.testclient import TestClient

from backend.app import app


def run_checks() -> Dict[str, Any]:
    client = TestClient(app)
    checks: List[Dict[str, Any]] = []

    def add(name: str, ok: bool, status: int | None = None, detail: str = "") -> None:
        checks.append({"name": name, "ok": bool(ok), "status": status, "detail": detail})

    def login(username: str, password: str) -> str:
        resp = client.post("/api/v1/auth/login", json={"username": username, "password": password})
        add(f"login_{username}", resp.status_code == 200, resp.status_code)
        token = resp.json().get("access_token", "") if resp.status_code == 200 else ""
        add(f"token_{username}_present", bool(token), resp.status_code)
        return token

    def wait_task(task_id: str, headers: Dict[str, str], timeout_sec: float = 10.0) -> Dict[str, Any]:
        deadline = time.time() + timeout_sec
        latest: Dict[str, Any] = {}
        while time.time() < deadline:
            resp = client.get(f"/api/v1/tasks/{task_id}", headers=headers)
            if resp.status_code == 200:
                latest = resp.json()
                if latest.get("status") in {"completed", "failed"}:
                    return latest
            time.sleep(0.1)
        return latest

    admin = login("admin", "admin123")
    analyst = login("analyst", "analyst123")
    admin_h = {"Authorization": f"Bearer {admin}"} if admin else {}
    analyst_h = {"Authorization": f"Bearer {analyst}"} if analyst else {}

    # Candidate v1 (gru) -> publish
    retrain_v1_submit = client.post(
        "/api/v1/tasks/model/retrain",
        json={"model_family": "gru", "trigger": "a1_6", "dry_run": True},
        headers=admin_h,
    )
    add("retrain_v1_submit_200", retrain_v1_submit.status_code == 200, retrain_v1_submit.status_code)
    retrain_v1_task = retrain_v1_submit.json().get("task_id", "") if retrain_v1_submit.status_code == 200 else ""
    add("retrain_v1_task_id_present", bool(retrain_v1_task), retrain_v1_submit.status_code)

    candidate_v1 = ""
    if retrain_v1_task:
        retrain_v1_status = wait_task(retrain_v1_task, admin_h)
        add("retrain_v1_completed", retrain_v1_status.get("status") == "completed", 200, retrain_v1_status.get("status", ""))
        candidate_v1 = (retrain_v1_status.get("result") or {}).get("candidate_version", "")
        add("candidate_v1_present", bool(candidate_v1), 200, candidate_v1)

    publish_v1_submit = client.post(
        "/api/v1/tasks/model/publish",
        json={"model_version": candidate_v1, "operator": "admin"},
        headers=admin_h,
    )
    add("publish_v1_submit_200", publish_v1_submit.status_code == 200, publish_v1_submit.status_code)
    publish_v1_task = publish_v1_submit.json().get("task_id", "") if publish_v1_submit.status_code == 200 else ""
    add("publish_v1_task_id_present", bool(publish_v1_task), publish_v1_submit.status_code)

    active_v1 = ""
    if publish_v1_task:
        publish_v1_status = wait_task(publish_v1_task, admin_h)
        add("publish_v1_completed", publish_v1_status.get("status") == "completed", 200, publish_v1_status.get("status", ""))
        active_v1 = (publish_v1_status.get("result") or {}).get("active_version", "")
        add("active_v1_present", bool(active_v1), 200, active_v1)

    # Candidate v2 (lstm) -> publish
    retrain_v2_submit = client.post(
        "/api/v1/tasks/model/retrain",
        json={"model_family": "lstm", "trigger": "a1_6", "dry_run": True},
        headers=admin_h,
    )
    add("retrain_v2_submit_200", retrain_v2_submit.status_code == 200, retrain_v2_submit.status_code)
    retrain_v2_task = retrain_v2_submit.json().get("task_id", "") if retrain_v2_submit.status_code == 200 else ""
    add("retrain_v2_task_id_present", bool(retrain_v2_task), retrain_v2_submit.status_code)

    candidate_v2 = ""
    if retrain_v2_task:
        retrain_v2_status = wait_task(retrain_v2_task, admin_h)
        add("retrain_v2_completed", retrain_v2_status.get("status") == "completed", 200, retrain_v2_status.get("status", ""))
        candidate_v2 = (retrain_v2_status.get("result") or {}).get("candidate_version", "")
        add("candidate_v2_present", bool(candidate_v2), 200, candidate_v2)

    publish_v2_submit = client.post(
        "/api/v1/tasks/model/publish",
        json={"model_version": candidate_v2, "operator": "admin"},
        headers=admin_h,
    )
    add("publish_v2_submit_200", publish_v2_submit.status_code == 200, publish_v2_submit.status_code)
    publish_v2_task = publish_v2_submit.json().get("task_id", "") if publish_v2_submit.status_code == 200 else ""
    add("publish_v2_task_id_present", bool(publish_v2_task), publish_v2_submit.status_code)

    active_v2 = ""
    if publish_v2_task:
        publish_v2_status = wait_task(publish_v2_task, admin_h)
        add("publish_v2_completed", publish_v2_status.get("status") == "completed", 200, publish_v2_status.get("status", ""))
        active_v2 = (publish_v2_status.get("result") or {}).get("active_version", "")
        add("active_v2_present", bool(active_v2), 200, active_v2)

    add("active_version_changed", bool(active_v1) and bool(active_v2) and active_v1 != active_v2, 200, f"{active_v1}->{active_v2}")

    # Rollback to v1
    rollback_submit = client.post(
        "/api/v1/tasks/model/rollback",
        json={"target_version": active_v1, "operator": "admin"},
        headers=admin_h,
    )
    add("rollback_submit_200", rollback_submit.status_code == 200, rollback_submit.status_code)
    rollback_task = rollback_submit.json().get("task_id", "") if rollback_submit.status_code == 200 else ""
    add("rollback_task_id_present", bool(rollback_task), rollback_submit.status_code)

    rollback_active = ""
    if rollback_task:
        rollback_status = wait_task(rollback_task, admin_h)
        add("rollback_completed", rollback_status.get("status") == "completed", 200, rollback_status.get("status", ""))
        rollback_result = rollback_status.get("result") or {}
        rollback_active = rollback_result.get("active_version", "")
        add("rollback_target_applied", rollback_active == active_v1, 200, f"{rollback_active} vs {active_v1}")

    registry = client.get("/api/v1/model/registry", headers=analyst_h)
    add("registry_200", registry.status_code == 200, registry.status_code)
    if registry.status_code == 200:
        payload = registry.json()
        reg_active = (payload.get("active") or {}).get("version", "")
        add("registry_active_after_rollback", reg_active == active_v1, registry.status_code, f"{reg_active} vs {active_v1}")
        history = payload.get("history") or []
        has_rollback = any((item.get("event") == "rollback") for item in history if isinstance(item, dict))
        add("registry_history_has_rollback", has_rollback, registry.status_code)

    health = client.get("/api/v1/model/health", headers=analyst_h)
    add("health_200", health.status_code == 200, health.status_code)
    if health.status_code == 200:
        add("health_status_healthy", health.json().get("status") == "healthy", health.status_code, health.json().get("status", ""))

    passed = sum(1 for item in checks if item["ok"])
    summary = {"pass": passed == len(checks), "total": len(checks), "passed": passed, "failed": len(checks) - passed}
    return {"checks": checks, "summary": summary}


def main() -> int:
    result = run_checks()
    output_dir = Path("model/registry")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "a1_6_rollback_result.json"
    output_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result["summary"], ensure_ascii=False))
    print(f"result_file={output_path.as_posix()}")
    return 0 if result["summary"]["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

