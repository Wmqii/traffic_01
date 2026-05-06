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
        if resp.status_code != 200:
            return ""
        token = resp.json().get("access_token", "")
        add(f"token_{username}_present", bool(token), resp.status_code)
        return token

    def wait_task(task_id: str, headers: Dict[str, str], timeout_sec: float = 8.0) -> Dict[str, Any]:
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

    viewer = login("viewer", "viewer123")
    analyst = login("analyst", "analyst123")
    admin = login("admin", "admin123")

    viewer_h = {"Authorization": f"Bearer {viewer}"} if viewer else {}
    analyst_h = {"Authorization": f"Bearer {analyst}"} if analyst else {}
    admin_h = {"Authorization": f"Bearer {admin}"} if admin else {}

    # RBAC for health endpoint: viewer should be forbidden.
    viewer_health = client.get("/api/v1/model/health", headers=viewer_h)
    add("model_health_viewer_403", viewer_health.status_code == 403, viewer_health.status_code)

    retrain_submit = client.post(
        "/api/v1/tasks/model/retrain",
        json={"model_family": "gru", "trigger": "manual", "dry_run": True},
        headers=admin_h,
    )
    add("model_retrain_submit_200", retrain_submit.status_code == 200, retrain_submit.status_code)
    retrain_task_id = retrain_submit.json().get("task_id", "") if retrain_submit.status_code == 200 else ""
    add("model_retrain_task_id_present", bool(retrain_task_id), retrain_submit.status_code)

    candidate_version = ""
    if retrain_task_id:
        retrain_status = wait_task(retrain_task_id, admin_h)
        retrain_state = retrain_status.get("status", "")
        retrain_result = retrain_status.get("result") or {}
        candidate_version = retrain_result.get("candidate_version", "")
        add("model_retrain_task_completed", retrain_state == "completed", 200, retrain_state)
        add("model_retrain_candidate_present", bool(candidate_version), 200, candidate_version)

    publish_submit = client.post(
        "/api/v1/tasks/model/publish",
        json={"model_version": candidate_version, "operator": "admin"},
        headers=admin_h,
    )
    add("model_publish_submit_200", publish_submit.status_code == 200, publish_submit.status_code)
    publish_task_id = publish_submit.json().get("task_id", "") if publish_submit.status_code == 200 else ""
    add("model_publish_task_id_present", bool(publish_task_id), publish_submit.status_code)

    active_version = ""
    if publish_task_id:
        publish_status = wait_task(publish_task_id, admin_h)
        publish_state = publish_status.get("status", "")
        publish_result = publish_status.get("result") or {}
        active_version = publish_result.get("active_version", "")
        add("model_publish_task_completed", publish_state == "completed", 200, publish_state)
        add("model_publish_active_version", bool(active_version), 200, active_version)

    health_sync = client.get("/api/v1/model/health", headers=analyst_h)
    add("model_health_sync_200", health_sync.status_code == 200, health_sync.status_code)
    health_ok = False
    if health_sync.status_code == 200:
        status = health_sync.json().get("status", "")
        health_ok = status == "healthy"
        add("model_health_sync_healthy", health_ok, health_sync.status_code, status)

    health_task_submit = client.post("/api/v1/tasks/model/health-check", headers=analyst_h)
    add("model_health_task_submit_200", health_task_submit.status_code == 200, health_task_submit.status_code)
    health_task_id = health_task_submit.json().get("task_id", "") if health_task_submit.status_code == 200 else ""
    add("model_health_task_id_present", bool(health_task_id), health_task_submit.status_code)
    if health_task_id:
        health_task_status = wait_task(health_task_id, analyst_h)
        add(
            "model_health_task_completed",
            health_task_status.get("status") == "completed",
            200,
            health_task_status.get("status", ""),
        )

    registry_resp = client.get("/api/v1/model/registry", headers=analyst_h)
    add("model_registry_200", registry_resp.status_code == 200, registry_resp.status_code)
    if registry_resp.status_code == 200:
        registry_json = registry_resp.json()
        registry_active = (registry_json.get("active") or {}).get("version", "")
        add("model_registry_active_match", registry_active == active_version, 200, f"{registry_active} vs {active_version}")
        add("model_registry_has_candidates_field", "candidates" in registry_json, 200)

    passed = sum(1 for item in checks if item["ok"])
    summary = {
        "pass": passed == len(checks),
        "total": len(checks),
        "passed": passed,
        "failed": len(checks) - passed,
    }
    return {"checks": checks, "summary": summary}


def main() -> int:
    result = run_checks()
    output_dir = Path("backend/tests/output")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "b1_4_scheduler_result.json"
    output_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result["summary"], ensure_ascii=False))
    print(f"result_file={output_path.as_posix()}")
    return 0 if result["summary"]["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

