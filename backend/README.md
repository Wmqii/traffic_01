# B1 Backend

## Install

```powershell
pip install fastapi uvicorn pydantic pyjwt
```

Optional (Redis cache backend):

```powershell
pip install redis
```

## Run API

```powershell
cd d:\小桌面\交通拥堵
$env:PYTHONPATH='.'
uvicorn backend.app:app --reload --port 8000
```

Docs:
- Swagger: `http://127.0.0.1:8000/api/v1/docs`
- OpenAPI JSON (runtime): `http://127.0.0.1:8000/api/v1/openapi.json`

## Export OpenAPI File

```powershell
cd d:\小桌面\交通拥堵
$env:PYTHONPATH='.'
$env:PYTHONIOENCODING='utf-8'
python backend/export_openapi.py
```

Generates `backend/openapi.json`.

## API Automation (T1-2)

Run API automation suite and generate structured result file:

```powershell
cd d:\小桌面\交通拥堵
$env:PYTHONPATH='.'
python backend/tests/api_automation_runner.py
```

Output:
- `backend/tests/output/t1_2_api_test_result.json`

## Performance Baseline (T1-4)

Run performance baseline for core APIs and map cache:

```powershell
cd d:\小桌面\交通拥堵
$env:PYTHONPATH='.'
python backend/tests/performance_runner.py
```

Output:
- `backend/tests/output/t1_4_perf_result.json`

## Scheduler APIs (B1-4)

Run B1-4 scheduler validation:

```powershell
cd d:\小桌面\交通拥堵
$env:PYTHONPATH='.'
python backend/tests/b1_4_scheduler_runner.py
```

Output:
- `backend/tests/output/b1_4_scheduler_result.json`

## Audit + Error Codes (B1-5)

Run B1-5 audit/error validation:

```powershell
cd d:\小桌面\交通拥堵
$env:PYTHONPATH='.'
python backend/tests/b1_5_audit_error_runner.py
```

Output:
- `backend/tests/output/b1_5_audit_error_result.json`

## Model Version Rollback (A1-6)

Run A1-6 version rollback drill:

```powershell
cd d:\小桌面\交通拥堵
$env:PYTHONPATH='.'
python backend/tests/a1_6_model_rollback_runner.py
```

Output:
- `model/registry/a1_6_rollback_result.json`

## Auth (B1-2)

### Login
`POST /api/v1/auth/login`

Sample body:
```json
{
  "username": "viewer",
  "password": "viewer123"
}
```

### Current user
`GET /api/v1/auth/me` with `Authorization: Bearer <token>`

### Demo accounts
- `admin / admin123` (admin)
- `analyst / analyst123` (analyst)
- `viewer / viewer123` (viewer)

## Core APIs (B1-1)
- `GET /health`
- `GET /api/v1/predictions/segments/{segment_id}` (`viewer+`)
- `GET /api/v1/congestion/events` (`viewer+`)
- `GET /api/v1/attributions/events/{event_id}` (`analyst+`)
- `GET /api/v1/map/layers/heat` (`viewer+`)
- `GET /api/v1/admin/audit` (`admin`)

## Cache + Async Tasks (B1-3)

### Environment variables
- `TRAFFIC_CACHE_BACKEND` (`auto` | `memory` | `redis`, default: `auto`)
- `TRAFFIC_CACHE_TTL_SECONDS` (default: `300`)
- `TRAFFIC_REDIS_URL` (default: `redis://127.0.0.1:6379/0`)

Behavior:
- `auto`: try Redis first, fallback to in-memory TTL cache.
- `redis`: try Redis, fallback to in-memory with fallback reason in stats.
- `memory`: always use in-memory TTL cache.

### APIs
- `GET /api/v1/cache/stats` (`admin`) - cache backend/hit/miss stats
- `POST /api/v1/cache/refresh/heat` (`analyst+`) - sync refresh heat-layer cache
- `POST /api/v1/tasks/cache/refresh-heat` (`analyst+`) - async refresh task submit
- `GET /api/v1/tasks/{task_id}` (`analyst+`) - query task status
- `GET /api/v1/tasks?limit=20` (`analyst+`) - list recent tasks

## Model Scheduling (B1-4)

### Files
- `backend/model_registry.py`
- `model/registry/model_registry.json` (auto-generated)

### APIs
- `POST /api/v1/tasks/model/retrain` (`admin`) - submit model retrain candidate task
- `POST /api/v1/tasks/model/publish` (`admin`) - publish candidate as active model
- `POST /api/v1/tasks/model/health-check` (`analyst+`) - submit async model health check
- `POST /api/v1/tasks/model/rollback` (`admin`) - rollback to target version
- `GET /api/v1/model/health` (`analyst+`) - fetch current model health snapshot
- `GET /api/v1/model/registry` (`analyst+`) - fetch active model + candidate snapshots

## Audit + Error Spec (B1-5)

### Files
- `backend/audit.py`
- `backend/error_codes.py`
- `backend/logs/audit.log` (runtime generated)

### Capabilities
- HTTP middleware records structured audit events with `request_id`, `status_code`, `duration_ms`.
- Standardized error envelope:
  - body: `error.code`, `error.message`, `error.request_id`, `error.detail`
  - headers: `X-Request-ID`, `X-Error-Code` (error only)

### APIs
- `GET /api/v1/admin/audit` (`admin`) - audit summary
- `GET /api/v1/admin/audit/events?limit=20` (`admin`) - recent audit events
