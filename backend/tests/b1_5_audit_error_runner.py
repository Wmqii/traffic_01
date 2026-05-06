from __future__ import annotations

import json
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
        token = ""
        if resp.status_code == 200:
            token = resp.json().get("access_token", "")
        add(f"token_{username}_present", bool(token), resp.status_code)
        return token

    # Error code: invalid credentials
    invalid_login = client.post("/api/v1/auth/login", json={"username": "viewer", "password": "bad"})
    add("invalid_login_401", invalid_login.status_code == 401, invalid_login.status_code)
    inv_json = invalid_login.json() if invalid_login.status_code == 401 else {}
    inv_code = ((inv_json.get("error") or {}).get("code")) if isinstance(inv_json, dict) else ""
    add("invalid_login_code", inv_code == "AUTH_INVALID_CREDENTIALS", invalid_login.status_code, str(inv_code))
    add("invalid_login_request_id_header", bool(invalid_login.headers.get("X-Request-ID")), invalid_login.status_code)

    admin = login("admin", "admin123")
    analyst = login("analyst", "analyst123")
    viewer = login("viewer", "viewer123")

    admin_h = {"Authorization": f"Bearer {admin}"} if admin else {}
    analyst_h = {"Authorization": f"Bearer {analyst}"} if analyst else {}
    viewer_h = {"Authorization": f"Bearer {viewer}"} if viewer else {}

    # Error code: forbidden
    viewer_audit = client.get("/api/v1/admin/audit", headers=viewer_h)
    add("viewer_audit_403", viewer_audit.status_code == 403, viewer_audit.status_code)
    viewer_code = ((viewer_audit.json().get("error") or {}).get("code")) if viewer_audit.status_code == 403 else ""
    add("viewer_audit_code", viewer_code == "AUTH_FORBIDDEN", viewer_audit.status_code, str(viewer_code))

    # Error code: task not found
    not_found_task = client.get("/api/v1/tasks/not-found-id", headers=analyst_h)
    add("task_not_found_404", not_found_task.status_code == 404, not_found_task.status_code)
    task_nf_code = ((not_found_task.json().get("error") or {}).get("code")) if not_found_task.status_code == 404 else ""
    add("task_not_found_code", task_nf_code == "TASK_NOT_FOUND", not_found_task.status_code, str(task_nf_code))

    # Validation error envelope
    invalid_body = client.post("/api/v1/auth/login", json={"username": "viewer"})
    add("validation_422", invalid_body.status_code == 422, invalid_body.status_code)
    val_code = ((invalid_body.json().get("error") or {}).get("code")) if invalid_body.status_code == 422 else ""
    add("validation_code", val_code == "VALIDATION_ERROR", invalid_body.status_code, str(val_code))

    # Audit APIs
    snapshot = client.get("/api/v1/admin/audit", headers=admin_h)
    add("audit_snapshot_200", snapshot.status_code == 200, snapshot.status_code)
    snap_json = snapshot.json() if snapshot.status_code == 200 else {}
    recent_count = int(snap_json.get("recent_event_count", 0)) if isinstance(snap_json, dict) else 0
    add("audit_snapshot_has_log_file", bool(snap_json.get("audit_log_file")), snapshot.status_code)
    add("audit_snapshot_recent_count_gt0", recent_count > 0, snapshot.status_code, str(recent_count))

    events = client.get("/api/v1/admin/audit/events?limit=10", headers=admin_h)
    add("audit_events_200", events.status_code == 200, events.status_code)
    event_list = events.json() if events.status_code == 200 else []
    add("audit_events_non_empty", isinstance(event_list, list) and len(event_list) > 0, events.status_code)
    if isinstance(event_list, list) and event_list:
        last = event_list[-1]
        add("audit_event_has_request_id", bool(last.get("request_id")), events.status_code)
        add("audit_event_has_status_code", isinstance(last.get("status_code"), int), events.status_code)
        add("audit_event_has_method_path", bool(last.get("method")) and bool(last.get("path")), events.status_code)

    passed = sum(1 for item in checks if item["ok"])
    summary = {"pass": passed == len(checks), "total": len(checks), "passed": passed, "failed": len(checks) - passed}
    return {"checks": checks, "summary": summary}


def main() -> int:
    result = run_checks()
    output_dir = Path("backend/tests/output")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "b1_5_audit_error_result.json"
    output_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result["summary"], ensure_ascii=False))
    print(f"result_file={output_path.as_posix()}")
    return 0 if result["summary"]["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

