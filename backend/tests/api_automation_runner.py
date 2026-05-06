from __future__ import annotations

import json
import sys
import time
from pathlib import Path
from typing import Any, Dict, List

from fastapi.testclient import TestClient

from backend.app import app


def run_checks() -> Dict[str, Any]:
    client = TestClient(app)
    checks: List[Dict[str, Any]] = []

    def add(name: str, ok: bool, status: int | None = None, detail: str = "") -> None:
        checks.append(
            {
                "name": name,
                "ok": bool(ok),
                "status": status,
                "detail": detail,
            }
        )

    def login(username: str, password: str) -> str:
        resp = client.post("/api/v1/auth/login", json={"username": username, "password": password})
        add(f"login_{username}", resp.status_code == 200, resp.status_code)
        if resp.status_code != 200:
            return ""
        token = resp.json().get("access_token", "")
        add(f"token_{username}_present", bool(token), resp.status_code)
        return token

    # Basic health and auth
    health = client.get("/health")
    add("health_200", health.status_code == 200, health.status_code)

    invalid_login = client.post("/api/v1/auth/login", json={"username": "viewer", "password": "wrong"})
    add("login_invalid_401", invalid_login.status_code == 401, invalid_login.status_code)

    viewer_token = login("viewer", "viewer123")
    analyst_token = login("analyst", "analyst123")
    admin_token = login("admin", "admin123")

    viewer_headers = {"Authorization": f"Bearer {viewer_token}"} if viewer_token else {}
    analyst_headers = {"Authorization": f"Bearer {analyst_token}"} if analyst_token else {}
    admin_headers = {"Authorization": f"Bearer {admin_token}"} if admin_token else {}

    me_resp = client.get("/api/v1/auth/me", headers=viewer_headers)
    add("auth_me_viewer_200", me_resp.status_code == 200, me_resp.status_code)

    # Core APIs
    pred_resp = client.get("/api/v1/predictions/segments/SEG-4001", headers=viewer_headers)
    add("prediction_viewer_200", pred_resp.status_code == 200, pred_resp.status_code)

    events_resp = client.get("/api/v1/congestion/events", headers=viewer_headers)
    events_json = events_resp.json() if events_resp.status_code == 200 else []
    add("events_viewer_200", events_resp.status_code == 200, events_resp.status_code)
    add("events_non_empty", isinstance(events_json, list) and len(events_json) > 0, events_resp.status_code)

    attribution_viewer = client.get("/api/v1/attributions/events/event-bridge")
    add("attribution_public_200", attribution_viewer.status_code == 200, attribution_viewer.status_code)

    attribution_analyst = client.get("/api/v1/attributions/events/event-bridge", headers=analyst_headers)
    add("attribution_analyst_200", attribution_analyst.status_code == 200, attribution_analyst.status_code)

    # Cache APIs
    heat_first = client.get("/api/v1/map/layers/heat", headers=viewer_headers)
    heat_second = client.get("/api/v1/map/layers/heat", headers=viewer_headers)
    add("heat_first_200", heat_first.status_code == 200, heat_first.status_code)
    add("heat_second_200", heat_second.status_code == 200, heat_second.status_code)

    cache_stats_viewer = client.get("/api/v1/cache/stats", headers=viewer_headers)
    add("cache_stats_viewer_403", cache_stats_viewer.status_code == 403, cache_stats_viewer.status_code)

    cache_stats_admin = client.get("/api/v1/cache/stats", headers=admin_headers)
    add("cache_stats_admin_200", cache_stats_admin.status_code == 200, cache_stats_admin.status_code)
    cache_stats_json = cache_stats_admin.json() if cache_stats_admin.status_code == 200 else {}
    hits = int(cache_stats_json.get("hits", 0)) if isinstance(cache_stats_json, dict) else 0
    misses = int(cache_stats_json.get("misses", 0)) if isinstance(cache_stats_json, dict) else 0
    add("cache_stats_has_hits_misses", hits >= 1 and misses >= 1, cache_stats_admin.status_code, f"hits={hits},misses={misses}")

    cache_refresh = client.post("/api/v1/cache/refresh/heat", headers=analyst_headers)
    add("cache_refresh_analyst_200", cache_refresh.status_code == 200, cache_refresh.status_code)

    analytics_overview = client.get("/api/v1/analytics/overview")
    add("analytics_overview_public_200", analytics_overview.status_code == 200, analytics_overview.status_code)
    overview_json = analytics_overview.json() if analytics_overview.status_code == 200 else []
    add("analytics_overview_non_empty", isinstance(overview_json, list) and len(overview_json) > 0, analytics_overview.status_code)

    analytics_trend = client.get("/api/v1/analytics/segments/SEG-4001/trend?points=12&window_minutes=15")
    add("analytics_trend_public_200", analytics_trend.status_code == 200, analytics_trend.status_code)

    analytics_causes = client.get("/api/v1/analytics/segments/SEG-4001/causes?points=8&window_minutes=15")
    add("analytics_causes_public_200", analytics_causes.status_code == 200, analytics_causes.status_code)

    analytics_prediction = client.get("/api/v1/analytics/segments/SEG-4001/prediction?history_points=12&future_points=8&window_minutes=15")
    add("analytics_prediction_public_200", analytics_prediction.status_code == 200, analytics_prediction.status_code)

    analytics_segment_predictions = client.get("/api/v1/analytics/predictions/segments?window_minutes=15")
    add("analytics_segment_predictions_public_200", analytics_segment_predictions.status_code == 200, analytics_segment_predictions.status_code)
    segment_predictions_json = analytics_segment_predictions.json() if analytics_segment_predictions.status_code == 200 else []
    add("analytics_segment_predictions_non_empty", isinstance(segment_predictions_json, list) and len(segment_predictions_json) > 0, analytics_segment_predictions.status_code)

    analytics_models = client.get("/api/v1/analytics/models/errors")
    add("analytics_model_errors_public_200", analytics_models.status_code == 200, analytics_models.status_code)
    models_json = analytics_models.json() if analytics_models.status_code == 200 else []
    add("analytics_model_errors_non_empty", isinstance(models_json, list) and len(models_json) > 0, analytics_models.status_code)

    analytics_report = client.get("/api/v1/analytics/segments/SEG-4001/report?window_minutes=15")
    add("analytics_report_public_200", analytics_report.status_code == 200, analytics_report.status_code)

    # Async task APIs
    submit_task = client.post("/api/v1/tasks/cache/refresh-heat", headers=analyst_headers)
    add("task_submit_200", submit_task.status_code == 200, submit_task.status_code)
    task_id = submit_task.json().get("task_id", "") if submit_task.status_code == 200 else ""
    add("task_id_present", bool(task_id), submit_task.status_code)

    task_status_ok = False
    task_status_code = None
    task_state = ""
    if task_id:
        for _ in range(30):
            status_resp = client.get(f"/api/v1/tasks/{task_id}", headers=analyst_headers)
            task_status_code = status_resp.status_code
            if status_resp.status_code == 200:
                task_state = status_resp.json().get("status", "")
                if task_state in {"completed", "failed"}:
                    task_status_ok = True
                    break
            time.sleep(0.1)
    add("task_status_terminal", task_status_ok, task_status_code, task_state)

    task_missing = client.get("/api/v1/tasks/not-found-id", headers=analyst_headers)
    add("task_not_found_404", task_missing.status_code == 404, task_missing.status_code)

    task_list = client.get("/api/v1/tasks?limit=20", headers=analyst_headers)
    add("task_list_200", task_list.status_code == 200, task_list.status_code)

    audit_no_auth = client.get("/api/v1/admin/audit")
    add("audit_no_auth_401", audit_no_auth.status_code == 401, audit_no_auth.status_code)

    audit_admin = client.get("/api/v1/admin/audit", headers=admin_headers)
    add("audit_admin_200", audit_admin.status_code == 200, audit_admin.status_code)
    endpoint_count = 0
    if audit_admin.status_code == 200:
        endpoint_count = int(audit_admin.json().get("endpoint_count", 0))
    add("audit_endpoint_count_valid", endpoint_count >= 10, audit_admin.status_code, str(endpoint_count))

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
    output_path = output_dir / "t1_2_api_test_result.json"
    output_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result["summary"], ensure_ascii=False))
    print(f"result_file={output_path.as_posix()}")
    return 0 if result["summary"]["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
