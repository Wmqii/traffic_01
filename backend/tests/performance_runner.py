from __future__ import annotations

import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi.testclient import TestClient

from backend.app import app


def percentile(values: List[float], p: float) -> float:
    if not values:
        return 0.0
    data = sorted(values)
    if len(data) == 1:
        return float(data[0])
    rank = (len(data) - 1) * (p / 100.0)
    low = int(rank)
    high = min(low + 1, len(data) - 1)
    weight = rank - low
    return data[low] * (1 - weight) + data[high] * weight


def run_load(
    client: TestClient,
    name: str,
    method: str,
    path: str,
    headers: Optional[Dict[str, str]] = None,
    total: int = 120,
    concurrency: int = 20,
) -> Dict[str, Any]:
    headers = headers or {}
    latencies_ms: List[float] = []
    status_codes: Dict[str, int] = {}
    failures: List[str] = []

    def one_call() -> tuple[int, float]:
        start = time.perf_counter()
        response = client.request(method, path, headers=headers)
        elapsed = (time.perf_counter() - start) * 1000.0
        return response.status_code, elapsed

    with ThreadPoolExecutor(max_workers=concurrency) as pool:
        futures = [pool.submit(one_call) for _ in range(total)]
        for fut in as_completed(futures):
            try:
                code, latency = fut.result()
                latencies_ms.append(latency)
                key = str(code)
                status_codes[key] = status_codes.get(key, 0) + 1
            except Exception as exc:  # pragma: no cover
                failures.append(str(exc))

    ok_count = sum(cnt for code, cnt in status_codes.items() if code.startswith("2"))
    total_count = max(len(latencies_ms), 1)
    success_rate = ok_count / total_count

    return {
        "name": name,
        "method": method,
        "path": path,
        "total_requests": total,
        "concurrency": concurrency,
        "status_codes": status_codes,
        "failures": failures,
        "latency_ms": {
            "min": round(min(latencies_ms) if latencies_ms else 0.0, 2),
            "p50": round(percentile(latencies_ms, 50), 2),
            "p95": round(percentile(latencies_ms, 95), 2),
            "p99": round(percentile(latencies_ms, 99), 2),
            "max": round(max(latencies_ms) if latencies_ms else 0.0, 2),
            "avg": round(sum(latencies_ms) / total_count, 2),
        },
        "success_rate": round(success_rate, 4),
    }


def main() -> int:
    client = TestClient(app)

    def login(username: str, password: str) -> str:
        resp = client.post("/api/v1/auth/login", json={"username": username, "password": password})
        if resp.status_code != 200:
            return ""
        return resp.json().get("access_token", "")

    viewer = login("viewer", "viewer123")
    analyst = login("analyst", "analyst123")
    admin = login("admin", "admin123")

    viewer_h = {"Authorization": f"Bearer {viewer}"} if viewer else {}
    analyst_h = {"Authorization": f"Bearer {analyst}"} if analyst else {}
    admin_h = {"Authorization": f"Bearer {admin}"} if admin else {}

    # Warm cache for map heat endpoint before cache-hit pressure test.
    client.get("/api/v1/map/layers/heat", headers=viewer_h)

    endpoints = [
        run_load(client, "prediction_segment", "GET", "/api/v1/predictions/segments/SEG-4001", viewer_h, 150, 25),
        run_load(client, "congestion_events", "GET", "/api/v1/congestion/events", viewer_h, 150, 25),
        run_load(client, "map_heat_cached", "GET", "/api/v1/map/layers/heat", viewer_h, 200, 30),
        run_load(client, "task_list", "GET", "/api/v1/tasks?limit=20", analyst_h, 120, 20),
        run_load(client, "audit_snapshot", "GET", "/api/v1/admin/audit", admin_h, 120, 20),
    ]

    gate_api_p95 = all(item["latency_ms"]["p95"] < 2000 for item in endpoints)
    gate_map_cached = next(item for item in endpoints if item["name"] == "map_heat_cached")["latency_ms"]["p95"] < 1000
    gate_success_rate = all(item["success_rate"] >= 0.99 for item in endpoints)

    result: Dict[str, Any] = {
        "meta": {
            "task_id": "T1-4",
            "run_mode": "local_testclient_pressure_baseline",
            "note": "当前版本无WebSocket接口（OpenAPI未暴露ws路径），本轮对接口与地图缓存链路执行压测基线。",
        },
        "endpoints": endpoints,
        "gates": {
            "api_p95_lt_2000ms": gate_api_p95,
            "map_cached_p95_lt_1000ms": gate_map_cached,
            "success_rate_ge_99pct": gate_success_rate,
        },
    }
    result["summary"] = {
        "pass": all(result["gates"].values()),
        "total_endpoints": len(endpoints),
        "failed_gates": [k for k, v in result["gates"].items() if not v],
    }

    out_dir = Path("backend/tests/output")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / "t1_4_perf_result.json"
    out_file.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    print(json.dumps(result["summary"], ensure_ascii=False))
    print("result_file=backend/tests/output/t1_4_perf_result.json")
    return 0 if result["summary"]["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

