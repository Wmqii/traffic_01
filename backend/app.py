import time
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List

import jwt
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel, Field

from .audit import audit_logger
from .auth import JWT_ALGORITHM, JWT_SECRET, authenticate_user, create_access_token, get_current_user, require_roles
from .cache import cache_service
from .data import repository
from .error_codes import (
    AUTH_INVALID_CREDENTIALS,
    INTERNAL_ERROR,
    RESOURCE_NOT_FOUND,
    TASK_NOT_FOUND,
    TASK_SUBMIT_FAILED,
    VALIDATION_ERROR,
    default_error_code,
)
from .model_registry import model_registry
from .tasks import task_manager

app = FastAPI(
    title="B1-1 核心 API",
    version="0.1.0",
    openapi_url="/api/v1/openapi.json",
    docs_url="/api/v1/docs",
    redoc_url="/api/v1/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5500",
        "http://localhost:5500",
        "http://127.0.0.1:15500",
        "http://localhost:15500",
        "http://127.0.0.1:25500",
        "http://localhost:25500",
        "http://127.0.0.1:3000",
        "http://localhost:3000",
        "http://127.0.0.1:8080",
        "http://localhost:8080",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID", "X-Error-Code"],
)


class FeatureSummaryItem(BaseModel):
    metric_name: str
    metric_value: float
    source: str


class SegmentPrediction(BaseModel):
    segment_id: str
    source: str
    window_start: datetime
    window_end: datetime
    predicted_congestion: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    feature_summary: List[FeatureSummaryItem]


class CongestionEvent(BaseModel):
    event_id: str
    segment_id: str
    name: str
    grid_id: str
    window_start: datetime
    window_end: datetime
    severity: str
    confidence: float = Field(..., ge=0.0, le=1.0)


class AttributionDriver(BaseModel):
    name: str
    source: str
    value: float
    impact: float
    notes: str


class EventAttribution(BaseModel):
    event_id: str
    segment_id: str
    generated_at: datetime
    predicted_severity: str
    drivers: List[AttributionDriver]


class HeatSegment(BaseModel):
    segment_id: str
    grid_id: str
    heat_score: float
    updated_at: datetime


class HeatLayer(BaseModel):
    layer_id: str
    generated_at: datetime
    segments: List[HeatSegment]


class SegmentOverviewItem(BaseModel):
    segment_id: str
    grid_id: str
    flow_veh_15m: float
    congestion_index: float = Field(..., ge=0.0, le=1.0)
    congestion_level: str
    updated_at: datetime


class SegmentTrendPoint(BaseModel):
    timestamp: datetime
    flow_veh_15m: float
    congestion_index: float = Field(..., ge=0.0, le=1.0)


class SegmentTrendResponse(BaseModel):
    segment_id: str
    window_minutes: int
    points: List[SegmentTrendPoint]


class CauseTimelinePoint(BaseModel):
    timestamp: datetime
    weather_pct: float
    holiday_pct: float
    incident_pct: float
    other_pct: float


class CauseRankingItem(BaseModel):
    cause: str
    contribution_pct: float


class SegmentCauseResponse(BaseModel):
    segment_id: str
    window_minutes: int
    timeline: List[CauseTimelinePoint]
    ranking: List[CauseRankingItem]
    summary: str


class PredictionFuturePoint(BaseModel):
    timestamp: datetime
    pred_flow_veh_15m: float
    pred_congestion_index: float = Field(..., ge=0.0, le=1.0)
    pred_congestion_level: str


class PredictionBacktestPoint(BaseModel):
    timestamp: datetime
    actual_flow_veh_15m: float
    pred_flow_veh_15m: float
    abs_error: float
    ape: float


class PredictionMetrics(BaseModel):
    mae: float
    mape: float
    rmse: float


class SegmentPredictionAnalysisResponse(BaseModel):
    segment_id: str
    window_minutes: int
    generated_at: datetime
    backtest: List[PredictionBacktestPoint]
    future: List[PredictionFuturePoint]
    metrics: PredictionMetrics


class ModelErrorItem(BaseModel):
    model_id: str
    model_name: str
    family: str
    mae: float
    mape: float
    rmse: float
    score: float


class SegmentAnalysisReportResponse(BaseModel):
    segment_id: str
    generated_at: datetime
    window_minutes: int
    findings: List[str]
    actions: List[str]


class SegmentGeometryItem(BaseModel):
    segment_id: str
    coordinates: List[List[float]]


class SegmentGeometryMeta(BaseModel):
    source: str
    segment_count: int
    file_path: str | None = None


class SegmentPredictionSnapshot(BaseModel):
    segment_id: str
    pred_flow_veh_15m: float
    pred_congestion_index: float = Field(..., ge=0.0, le=1.0)
    pred_congestion_level: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    window_start: datetime
    window_end: datetime


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_at: datetime
    role: str


class UserProfile(BaseModel):
    username: str
    role: str
    display_name: str


class AuditSnapshot(BaseModel):
    generated_at: datetime
    user_count: int
    endpoint_count: int
    audit_log_file: str | None = None
    recent_event_count: int | None = None
    error_event_count: int | None = None


class AuditEvent(BaseModel):
    event_id: str
    timestamp: datetime
    event_type: str
    request_id: str
    method: str
    path: str
    status_code: int
    duration_ms: float
    username: str | None = None
    role: str | None = None
    client_ip: str | None = None
    error_code: str | None = None


class ErrorBody(BaseModel):
    code: str
    message: str
    request_id: str
    detail: Any | None = None


class CacheStats(BaseModel):
    backend: str
    configured_backend: str
    default_ttl_seconds: int
    hits: int
    misses: int
    keys: int
    fallback_reason: str = ""


class CacheRefreshResult(BaseModel):
    refreshed_at: datetime
    cache_key: str
    segment_count: int
    ttl_seconds: int


class AsyncTaskSubmitResponse(BaseModel):
    task_id: str
    task_type: str
    status: str
    created_at: datetime


class AsyncTaskStatus(BaseModel):
    task_id: str
    task_type: str
    status: str
    created_at: datetime
    started_at: datetime | None = None
    finished_at: datetime | None = None
    result: Dict[str, Any] | None = None
    error: Dict[str, Any] | None = None


class ModelRetrainRequest(BaseModel):
    model_family: str = Field(default="gru")
    trigger: str = Field(default="manual")
    dry_run: bool = True


class ModelPublishRequest(BaseModel):
    model_version: str | None = None
    operator: str = Field(default="admin")


class ModelRollbackRequest(BaseModel):
    target_version: str | None = None
    operator: str = Field(default="admin")


class ModelHealthSnapshot(BaseModel):
    status: str
    checked_at: datetime
    active_version: str
    model_family: str
    metrics_exists: bool
    metrics_age_hours: float | None = None
    mape: float | None = None
    thresholds: Dict[str, float]


class ModelRegistrySnapshot(BaseModel):
    updated_at: datetime
    active: Dict[str, Any]
    candidates: List[Dict[str, Any]]
    last_health: Dict[str, Any] | None = None
    history: List[Dict[str, Any]] | None = None


HEAT_LAYER_CACHE_KEY = "map:layers:heat:v1"


def _refresh_heat_cache() -> Dict[str, Any]:
    heat_payload = repository.get_heat_layer()
    cache_service.set(HEAT_LAYER_CACHE_KEY, heat_payload)
    return {
        "refreshed_at": datetime.now(timezone.utc),
        "cache_key": HEAT_LAYER_CACHE_KEY,
        "segment_count": len(heat_payload.get("segments", [])),
        "ttl_seconds": cache_service.config.default_ttl,
    }


def _submit_model_retrain(payload: ModelRetrainRequest) -> Dict[str, Any]:
    return model_registry.submit_retrain(
        model_family=payload.model_family,
        trigger=payload.trigger,
        dry_run=payload.dry_run,
    )


def _submit_model_publish(payload: ModelPublishRequest) -> Dict[str, Any]:
    return model_registry.publish(
        model_version=payload.model_version,
        operator=payload.operator,
    )


def _submit_model_rollback(payload: ModelRollbackRequest) -> Dict[str, Any]:
    return model_registry.rollback(
        target_version=payload.target_version,
        operator=payload.operator,
    )


def _request_id(request: Request) -> str:
    rid = getattr(request.state, "request_id", "")
    if rid:
        return rid
    rid = request.headers.get("X-Request-ID", "")
    return rid or str(uuid.uuid4())


def _decode_principal(request: Request) -> tuple[str | None, str | None]:
    authz = request.headers.get("Authorization", "")
    if not authz.startswith("Bearer "):
        return None, None
    token = authz.split(" ", 1)[1].strip()
    if not token:
        return None, None
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        username = payload.get("sub")
        role = payload.get("role")
        return (str(username) if username else None, str(role) if role else None)
    except Exception:  # noqa: BLE001
        return None, None


def _error_response(
    request: Request,
    status_code: int,
    code: str,
    message: str,
    detail: Any | None = None,
) -> JSONResponse:
    rid = _request_id(request)
    body = {"error": ErrorBody(code=code, message=message, request_id=rid, detail=detail).model_dump()}
    return JSONResponse(status_code=status_code, content=body, headers={"X-Request-ID": rid, "X-Error-Code": code})


@app.middleware("http")
async def audit_middleware(request: Request, call_next):  # type: ignore[no-untyped-def]
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    request.state.request_id = request_id
    started = time.perf_counter()
    response: Response | None = None
    try:
        response = await call_next(request)
        return response
    finally:
        duration_ms = (time.perf_counter() - started) * 1000.0
        status_code = 500
        error_code = None
        if response is not None:
            status_code = response.status_code
            response.headers["X-Request-ID"] = request_id
            error_code = response.headers.get("X-Error-Code")
        if error_code is None and status_code >= 400:
            error_code = default_error_code(status_code)
        username, role = _decode_principal(request)
        client_ip = request.client.host if request.client else None
        audit_logger.log_http_request(
            request_id=request_id,
            method=request.method,
            path=request.url.path,
            status_code=status_code,
            duration_ms=duration_ms,
            username=username,
            role=role,
            client_ip=client_ip,
            error_code=error_code,
        )


@app.exception_handler(HTTPException)
async def handle_http_exception(request: Request, exc: HTTPException) -> JSONResponse:
    detail = exc.detail
    code = default_error_code(exc.status_code)
    message = "Request failed"
    extra: Any | None = None
    if isinstance(detail, dict):
        code = str(detail.get("code") or code)
        message = str(detail.get("message") or detail.get("detail") or message)
        extra = detail.get("detail")
    elif isinstance(detail, str):
        message = detail
    elif detail is not None:
        message = str(detail)
    return _error_response(request, exc.status_code, code, message, extra)


@app.exception_handler(RequestValidationError)
async def handle_validation_exception(request: Request, exc: RequestValidationError) -> JSONResponse:
    return _error_response(request, 422, VALIDATION_ERROR, "Request validation failed", exc.errors())


@app.exception_handler(Exception)
async def handle_internal_exception(request: Request, _: Exception) -> JSONResponse:
    return _error_response(request, 500, INTERNAL_ERROR, "Internal server error")


@app.get("/health")
def health_check() -> Dict[str, str]:
    return {"status": "ok", "timestamp": datetime.now(timezone.utc).isoformat()}


@app.post("/api/v1/auth/login", response_model=LoginResponse)
def login(payload: LoginRequest) -> LoginResponse:
    user = authenticate_user(payload.username, payload.password)
    if not user:
        raise HTTPException(
            status_code=401,
            detail={"code": AUTH_INVALID_CREDENTIALS, "message": "Invalid username or password"},
        )
    token, expires_at = create_access_token(user["username"], user["role"])
    return LoginResponse(access_token=token, expires_at=expires_at, role=user["role"])


@app.get("/api/v1/auth/me", response_model=UserProfile)
def me(user: Dict[str, str] = Depends(get_current_user)) -> UserProfile:
    return UserProfile(**user)


@app.get(
    "/api/v1/predictions/segments/{segment_id}",
    response_model=SegmentPrediction,
    response_model_exclude_none=True,
)
def get_segment_prediction(
    segment_id: str,
) -> SegmentPrediction:
    prediction = repository.get_segment_predictions(segment_id)
    if not prediction:
        raise HTTPException(status_code=404, detail={"code": RESOURCE_NOT_FOUND, "message": "Segment not found"})
    return SegmentPrediction(**prediction)


@app.get(
    "/api/v1/congestion/events",
    response_model=List[CongestionEvent],
    response_model_exclude_none=True,
)
def list_congestion_events(
) -> List[CongestionEvent]:
    return [CongestionEvent(**event) for event in repository.list_congestion_events()]


@app.get(
    "/api/v1/attributions/events/{event_id}",
    response_model=EventAttribution,
    response_model_exclude_none=True,
)
def get_event_attribution(
    event_id: str,
) -> EventAttribution:
    attribution = repository.get_event_attribution(event_id)
    if not attribution:
        raise HTTPException(status_code=404, detail={"code": RESOURCE_NOT_FOUND, "message": "Event not found"})
    return EventAttribution(**attribution)


@app.get(
    "/api/v1/map/layers/heat",
    response_model=HeatLayer,
    response_model_exclude_none=True,
)
def get_heat_layer(
) -> HeatLayer:
    cached = cache_service.get(HEAT_LAYER_CACHE_KEY)
    if cached is not None:
        return HeatLayer(**cached)
    payload = repository.get_heat_layer()
    cache_service.set(HEAT_LAYER_CACHE_KEY, payload)
    return HeatLayer(**payload)


@app.get(
    "/api/v1/analytics/overview",
    response_model=List[SegmentOverviewItem],
    response_model_exclude_none=True,
)
def get_overview(window_minutes: int = 15) -> List[SegmentOverviewItem]:
    records = repository.list_segment_overview(window_minutes=window_minutes)
    return [SegmentOverviewItem(**item) for item in records]


@app.get(
    "/api/v1/analytics/segments/{segment_id}/trend",
    response_model=SegmentTrendResponse,
    response_model_exclude_none=True,
)
def get_segment_trend(
    segment_id: str,
    points: int = 12,
    window_minutes: int = 15,
) -> SegmentTrendResponse:
    payload = repository.get_segment_trend(segment_id, points=points, window_minutes=window_minutes)
    if not payload:
        raise HTTPException(status_code=404, detail={"code": RESOURCE_NOT_FOUND, "message": "Segment not found"})
    return SegmentTrendResponse(**payload)


@app.get(
    "/api/v1/analytics/segments/{segment_id}/causes",
    response_model=SegmentCauseResponse,
    response_model_exclude_none=True,
)
def get_segment_causes(
    segment_id: str,
    points: int = 8,
    window_minutes: int = 15,
) -> SegmentCauseResponse:
    payload = repository.get_segment_causes(segment_id, points=points, window_minutes=window_minutes)
    if not payload:
        raise HTTPException(status_code=404, detail={"code": RESOURCE_NOT_FOUND, "message": "Segment not found"})
    return SegmentCauseResponse(**payload)


@app.get(
    "/api/v1/analytics/segments/{segment_id}/prediction",
    response_model=SegmentPredictionAnalysisResponse,
    response_model_exclude_none=True,
)
def get_segment_prediction_analysis(
    segment_id: str,
    history_points: int = 12,
    future_points: int = 8,
    window_minutes: int = 15,
) -> SegmentPredictionAnalysisResponse:
    payload = repository.get_segment_prediction_analysis(
        segment_id,
        history_points=history_points,
        future_points=future_points,
        window_minutes=window_minutes,
    )
    if not payload:
        raise HTTPException(status_code=404, detail={"code": RESOURCE_NOT_FOUND, "message": "Segment not found"})
    return SegmentPredictionAnalysisResponse(**payload)


@app.get(
    "/api/v1/analytics/models/errors",
    response_model=List[ModelErrorItem],
    response_model_exclude_none=True,
)
def get_model_error_comparison() -> List[ModelErrorItem]:
    rows = repository.get_model_error_comparison()
    return [ModelErrorItem(**item) for item in rows]


@app.get(
    "/api/v1/analytics/segments/{segment_id}/report",
    response_model=SegmentAnalysisReportResponse,
    response_model_exclude_none=True,
)
def get_segment_analysis_report(
    segment_id: str,
    window_minutes: int = 15,
) -> SegmentAnalysisReportResponse:
    payload = repository.get_segment_analysis_report(segment_id=segment_id, window_minutes=window_minutes)
    if not payload:
        raise HTTPException(status_code=404, detail={"code": RESOURCE_NOT_FOUND, "message": "Segment not found"})
    return SegmentAnalysisReportResponse(**payload)


@app.get(
    "/api/v1/map/segments/geometry",
    response_model=List[SegmentGeometryItem],
    response_model_exclude_none=True,
)
def get_segment_geometries() -> List[SegmentGeometryItem]:
    rows = repository.get_segment_geometries()
    return [SegmentGeometryItem(**item) for item in rows]


@app.get(
    "/api/v1/map/segments/geometry/meta",
    response_model=SegmentGeometryMeta,
    response_model_exclude_none=True,
)
def get_segment_geometry_meta() -> SegmentGeometryMeta:
    return SegmentGeometryMeta(**repository.get_segment_geometry_meta())


@app.get(
    "/api/v1/analytics/predictions/segments",
    response_model=List[SegmentPredictionSnapshot],
    response_model_exclude_none=True,
)
def list_segment_prediction_snapshots(window_minutes: int = 15) -> List[SegmentPredictionSnapshot]:
    rows = repository.list_segment_prediction_snapshots(window_minutes=window_minutes)
    return [SegmentPredictionSnapshot(**item) for item in rows]


@app.get("/api/v1/cache/stats", response_model=CacheStats)
def get_cache_stats(
    _: Dict[str, str] = Depends(require_roles("admin")),
) -> CacheStats:
    return CacheStats(**cache_service.stats())


@app.post("/api/v1/cache/refresh/heat", response_model=CacheRefreshResult)
def refresh_heat_cache(
    _: Dict[str, str] = Depends(require_roles("analyst", "admin")),
) -> CacheRefreshResult:
    return CacheRefreshResult(**_refresh_heat_cache())


@app.post("/api/v1/tasks/cache/refresh-heat", response_model=AsyncTaskSubmitResponse)
def submit_refresh_heat_task(
    _: Dict[str, str] = Depends(require_roles("analyst", "admin")),
) -> AsyncTaskSubmitResponse:
    task_id = task_manager.submit("refresh_heat_cache", _refresh_heat_cache)
    task_record = task_manager.get(task_id)
    if not task_record:
        raise HTTPException(status_code=500, detail={"code": TASK_SUBMIT_FAILED, "message": "Task submit failed"})
    return AsyncTaskSubmitResponse(
        task_id=task_record["task_id"],
        task_type=task_record["task_type"],
        status=task_record["status"],
        created_at=task_record["created_at"],
    )


@app.get("/api/v1/tasks/{task_id}", response_model=AsyncTaskStatus)
def get_task_status(
    task_id: str,
    _: Dict[str, str] = Depends(require_roles("analyst", "admin")),
) -> AsyncTaskStatus:
    task_record = task_manager.get(task_id)
    if not task_record:
        raise HTTPException(status_code=404, detail={"code": TASK_NOT_FOUND, "message": "Task not found"})
    return AsyncTaskStatus(**task_record)


@app.get("/api/v1/tasks", response_model=List[AsyncTaskStatus])
def list_tasks(
    limit: int = 20,
    _: Dict[str, str] = Depends(require_roles("analyst", "admin")),
) -> List[AsyncTaskStatus]:
    limit = max(1, min(limit, 100))
    return [AsyncTaskStatus(**item) for item in task_manager.list_recent(limit)]


@app.post("/api/v1/tasks/model/retrain", response_model=AsyncTaskSubmitResponse)
def submit_model_retrain_task(
    payload: ModelRetrainRequest,
    _: Dict[str, str] = Depends(require_roles("admin")),
) -> AsyncTaskSubmitResponse:
    task_id = task_manager.submit("model_retrain", lambda: _submit_model_retrain(payload))
    task_record = task_manager.get(task_id)
    if not task_record:
        raise HTTPException(status_code=500, detail={"code": TASK_SUBMIT_FAILED, "message": "Task submit failed"})
    return AsyncTaskSubmitResponse(
        task_id=task_record["task_id"],
        task_type=task_record["task_type"],
        status=task_record["status"],
        created_at=task_record["created_at"],
    )


@app.post("/api/v1/tasks/model/publish", response_model=AsyncTaskSubmitResponse)
def submit_model_publish_task(
    payload: ModelPublishRequest,
    _: Dict[str, str] = Depends(require_roles("admin")),
) -> AsyncTaskSubmitResponse:
    task_id = task_manager.submit("model_publish", lambda: _submit_model_publish(payload))
    task_record = task_manager.get(task_id)
    if not task_record:
        raise HTTPException(status_code=500, detail={"code": TASK_SUBMIT_FAILED, "message": "Task submit failed"})
    return AsyncTaskSubmitResponse(
        task_id=task_record["task_id"],
        task_type=task_record["task_type"],
        status=task_record["status"],
        created_at=task_record["created_at"],
    )


@app.post("/api/v1/tasks/model/health-check", response_model=AsyncTaskSubmitResponse)
def submit_model_health_task(
    _: Dict[str, str] = Depends(require_roles("analyst", "admin")),
) -> AsyncTaskSubmitResponse:
    task_id = task_manager.submit("model_health_check", model_registry.health_check)
    task_record = task_manager.get(task_id)
    if not task_record:
        raise HTTPException(status_code=500, detail={"code": TASK_SUBMIT_FAILED, "message": "Task submit failed"})
    return AsyncTaskSubmitResponse(
        task_id=task_record["task_id"],
        task_type=task_record["task_type"],
        status=task_record["status"],
        created_at=task_record["created_at"],
    )


@app.post("/api/v1/tasks/model/rollback", response_model=AsyncTaskSubmitResponse)
def submit_model_rollback_task(
    payload: ModelRollbackRequest,
    _: Dict[str, str] = Depends(require_roles("admin")),
) -> AsyncTaskSubmitResponse:
    task_id = task_manager.submit("model_rollback", lambda: _submit_model_rollback(payload))
    task_record = task_manager.get(task_id)
    if not task_record:
        raise HTTPException(status_code=500, detail={"code": TASK_SUBMIT_FAILED, "message": "Task submit failed"})
    return AsyncTaskSubmitResponse(
        task_id=task_record["task_id"],
        task_type=task_record["task_type"],
        status=task_record["status"],
        created_at=task_record["created_at"],
    )


@app.get("/api/v1/model/health", response_model=ModelHealthSnapshot)
def get_model_health(
    _: Dict[str, str] = Depends(require_roles("analyst", "admin")),
) -> ModelHealthSnapshot:
    return ModelHealthSnapshot(**model_registry.health_check())


@app.get("/api/v1/model/registry", response_model=ModelRegistrySnapshot)
def get_model_registry(
    _: Dict[str, str] = Depends(require_roles("analyst", "admin")),
) -> ModelRegistrySnapshot:
    snapshot = model_registry.snapshot()
    return ModelRegistrySnapshot(
        updated_at=snapshot["updated_at"],
        active=snapshot.get("active", {}),
        candidates=snapshot.get("candidates", []),
        last_health=snapshot.get("last_health"),
        history=snapshot.get("history", []),
    )


@app.get("/api/v1/admin/audit", response_model=AuditSnapshot)
def get_audit_snapshot(
    _: Dict[str, str] = Depends(require_roles("admin")),
) -> AuditSnapshot:
    endpoint_count = len(
        [
            route
            for route in app.routes
            if getattr(route, "path", "").startswith("/api/v1") or getattr(route, "path", "") == "/health"
        ]
    )
    recent_events = audit_logger.tail(limit=50)
    error_events = [item for item in recent_events if item.get("error_code")]
    return AuditSnapshot(
        generated_at=datetime.now(timezone.utc),
        user_count=3,
        endpoint_count=endpoint_count,
        audit_log_file=str(audit_logger.log_path),
        recent_event_count=len(recent_events),
        error_event_count=len(error_events),
    )


@app.get("/api/v1/admin/audit/events", response_model=List[AuditEvent])
def list_audit_events(
    limit: int = 20,
    _: Dict[str, str] = Depends(require_roles("admin")),
) -> List[AuditEvent]:
    limit = max(1, min(limit, 200))
    events = audit_logger.tail(limit=limit)
    return [AuditEvent(**event) for event in events]
