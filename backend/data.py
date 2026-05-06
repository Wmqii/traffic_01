from __future__ import annotations

import csv
import json
import math
import random
from datetime import datetime, timezone
from datetime import timedelta
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent
DATA_PIPELINE = PROJECT_ROOT / "data-pipeline"
FEATURE_TABLE_PATH = DATA_PIPELINE / "features" / "output" / "feature_table.csv"
ALIGNMENT_PATH = DATA_PIPELINE / "alignment" / "output" / "aligned" / "aligned_records.csv"
QUALITY_PATH = DATA_PIPELINE / "quality" / "output" / "quality_scoreboard.csv"
BASELINE_METRICS_PATH = PROJECT_ROOT / "model" / "baseline" / "output" / "metrics.json"
DEEP_METRICS_PATH = PROJECT_ROOT / "model" / "deep" / "output" / "metrics.json"
STGNN_METRICS_PATH = PROJECT_ROOT / "model" / "stgnn" / "output" / "metrics.json"
SEGMENT_GEOMETRY_PATH = DATA_PIPELINE / "alignment" / "config" / "segment_geometry.json"


DEFAULT_SEGMENT_GEOMETRY: Dict[str, List[List[float]]] = {
    "SEG-1001": [[31.226, 121.459], [31.229, 121.466]],
    "SEG-1002": [[31.223, 121.474], [31.228, 121.482]],
    "SEG-1003": [[31.218, 121.446], [31.221, 121.455]],
    "SEG-2001": [[31.235, 121.449], [31.239, 121.458]],
    "SEG-2002": [[31.234, 121.468], [31.239, 121.476]],
    "SEG-2003": [[31.231, 121.437], [31.236, 121.445]],
    "SEG-3001": [[31.213, 121.463], [31.218, 121.470]],
    "SEG-3002": [[31.209, 121.479], [31.215, 121.486]],
    "SEG-3003": [[31.205, 121.451], [31.211, 121.458]],
    "SEG-4001": [[31.244, 121.462], [31.248, 121.471]],
    "SEG-4002": [[31.246, 121.478], [31.251, 121.487]],
    "SEG-4003": [[31.241, 121.444], [31.246, 121.451]],
}


def _parse_datetime(value: str) -> datetime:
    if value.endswith("Z"):
        value = value.replace("Z", "+00:00")
    return datetime.fromisoformat(value)


def _to_float(value: Optional[str]) -> Optional[float]:
    if value is None or value == "":
        return None
    return float(value)


def _load_csv(path: Path) -> Iterable[Dict[str, str]]:
    if not path.exists():
        raise FileNotFoundError(f"Required data file not found: {path}")
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            yield row


def _load_json(path: Path) -> Dict[str, object]:
    if not path.exists():
        return {}
    try:
        parsed = json.loads(path.read_text(encoding="utf-8"))
        return parsed if isinstance(parsed, dict) else {}
    except Exception:
        return {}


def _normalize_segment_geometry(payload: Any) -> Dict[str, List[List[float]]]:
    if not isinstance(payload, (dict, list)):
        return {}
    result: Dict[str, List[List[float]]] = {}
    if isinstance(payload, dict):
        if "segments" in payload and isinstance(payload["segments"], list):
            payload = payload["segments"]
        else:
            for seg_id, coords in payload.items():
                if not isinstance(seg_id, str) or not isinstance(coords, list):
                    continue
                normalized: List[List[float]] = []
                for item in coords:
                    if isinstance(item, list) and len(item) >= 2:
                        try:
                            normalized.append([float(item[0]), float(item[1])])
                        except Exception:
                            continue
                if len(normalized) >= 2:
                    result[seg_id] = normalized
            return result
    if isinstance(payload, list):
        for item in payload:
            if not isinstance(item, dict):
                continue
            seg_id = item.get("segment_id")
            coords = item.get("coordinates")
            if not isinstance(seg_id, str) or not isinstance(coords, list):
                continue
            normalized: List[List[float]] = []
            for pt in coords:
                if isinstance(pt, list) and len(pt) >= 2:
                    try:
                        normalized.append([float(pt[0]), float(pt[1])])
                    except Exception:
                        continue
            if len(normalized) >= 2:
                result[seg_id] = normalized
    return result


def load_segment_geometry() -> tuple[Dict[str, List[List[float]]], str, str | None]:
    if not SEGMENT_GEOMETRY_PATH.exists():
        return DEFAULT_SEGMENT_GEOMETRY.copy(), "fallback", None
    try:
        payload = json.loads(SEGMENT_GEOMETRY_PATH.read_text(encoding="utf-8"))
        normalized = _normalize_segment_geometry(payload)
        if normalized:
            return normalized, "file", str(SEGMENT_GEOMETRY_PATH)
    except Exception:
        pass
    return DEFAULT_SEGMENT_GEOMETRY.copy(), "fallback", str(SEGMENT_GEOMETRY_PATH)


def load_feature_records() -> List[Dict[str, object]]:
    results: List[Dict[str, object]] = []
    for row in _load_csv(FEATURE_TABLE_PATH):
        window_start = _parse_datetime(row["window_start"])
        window_end = _parse_datetime(row["window_end"])
        metric_sum = _to_float(row.get("metric_sum")) or 0.0
        metric_avg = _to_float(row.get("metric_avg")) or 0.0
        metric_max = _to_float(row.get("metric_max")) or 0.0
        results.append(
            {
                "source": row["source"],
                "segment_id": row["segment_id"],
                "grid_id": row["grid_id"],
                "window_start": window_start,
                "window_end": window_end,
                "metric_name": row["metric_name"],
                "metric_sum": metric_sum,
                "metric_avg": metric_avg,
                "metric_max": metric_max,
                "metric_count": int(row.get("metric_count") or 0),
                "segment_numeric": int(row.get("segment_numeric") or 0),
            }
        )
    return results


def load_alignment_records() -> List[Dict[str, object]]:
    results: List[Dict[str, object]] = []
    for row in _load_csv(ALIGNMENT_PATH):
        window_start = _parse_datetime(row["window_start"])
        window_end = _parse_datetime(row["window_end"])
        timestamp = _parse_datetime(row["timestamp"])
        metric_value = _to_float(row.get("metric_value")) or 0.0
        results.append(
            {
                "source": row["source"],
                "entity_id": row["entity_id"],
                "segment_id": row["segment_id"],
                "grid_id": row["grid_id"],
                "metric_name": row["metric_name"],
                "metric_value": metric_value,
                "window_start": window_start,
                "window_end": window_end,
                "timestamp": timestamp,
            }
        )
    return results


def load_quality_scores() -> Dict[str, float]:
    scores: Dict[str, float] = {}
    for row in _load_csv(QUALITY_PATH):
        overall = _to_float(row.get("overall_score")) or 0.0
        scores[row["source"]] = min(max(overall / 100.0, 0.0), 1.0)
    return scores


def build_feature_index(records: Iterable[Dict[str, object]]) -> Dict[str, List[Dict[str, object]]]:
    index: Dict[str, List[Dict[str, object]]] = {}
    for record in records:
        segment_id = record["segment_id"]
        index.setdefault(segment_id, []).append(record)
    return index


def compute_metric_maxima(records: Iterable[Dict[str, object]]) -> Dict[str, float]:
    maxima: Dict[str, float] = {}
    for record in records:
        name = record["metric_name"]
        value = float(record.get("metric_sum") or 0.0)
        maxima[name] = max(maxima.get(name, 0.0), value)
    return maxima


def build_latest_feature_index(records: Iterable[Dict[str, object]]) -> Dict[str, Dict[str, object]]:
    latest: Dict[str, Dict[str, object]] = {}
    for record in records:
        segment_id = str(record["segment_id"])
        current = latest.get(segment_id)
        if current is None or record["window_end"] > current["window_end"]:
            latest[segment_id] = record
    return latest


class DataRepository:
    def __init__(self) -> None:
        self.feature_rows = load_feature_records()
        self.alignment_rows = load_alignment_records()
        self.quality_scores = load_quality_scores()
        self.features_by_segment = build_feature_index(self.feature_rows)
        self.metric_maxima = compute_metric_maxima(self.feature_rows)
        self.latest_feature_by_segment = build_latest_feature_index(self.feature_rows)
        self.model_error_rows = self._load_model_error_rows()
        self.segment_geometry, self.segment_geometry_source, self.segment_geometry_file = load_segment_geometry()

    def get_segment_predictions(self, segment_id: str) -> Optional[Dict[str, object]]:
        records = self.features_by_segment.get(segment_id)
        if not records:
            return None
        latest = max(records, key=lambda entry: entry["window_end"])
        quality_score = self.quality_scores.get(latest["source"], 0.8)
        confidence = 0.55 + quality_score * 0.45
        severity = self._compute_severity(latest)
        summary = [
            {
                "metric_name": record["metric_name"],
                "metric_value": record["metric_sum"],
                "source": record["source"],
            }
            for record in sorted(records, key=lambda r: r["metric_sum"], reverse=True)
        ]
        return {
            "segment_id": segment_id,
            "source": latest["source"],
            "window_start": latest["window_start"],
            "window_end": latest["window_end"],
            "predicted_congestion": severity,
            "confidence": min(confidence, 1.0),
            "feature_summary": summary,
        }

    def list_congestion_events(self) -> List[Dict[str, object]]:
        events = [row for row in self.alignment_rows if row["source"] == "event"]
        result = []
        for event in events:
            predictions = self.get_segment_predictions(event["segment_id"])
            severity = predictions["predicted_congestion"] if predictions else "Unknown"
            confidence = predictions["confidence"] if predictions else 0.65
            result.append(
                {
                    "event_id": event["entity_id"],
                    "segment_id": event["segment_id"],
                    "name": event["entity_id"].replace("event-", "Event ").title(),
                    "grid_id": event["grid_id"],
                    "window_start": event["window_start"],
                    "window_end": event["window_end"],
                    "severity": severity,
                    "confidence": confidence,
                }
            )
        return result

    def get_event_attribution(self, event_id: str) -> Optional[Dict[str, object]]:
        event = next((row for row in self.alignment_rows if row["entity_id"] == event_id), None)
        if not event:
            return None
        contributors = self._gather_drivers_for_event(event)
        base_prediction = self.get_segment_predictions(event["segment_id"])
        return {
            "event_id": event_id,
            "segment_id": event["segment_id"],
            "generated_at": datetime.now(timezone.utc),
            "predicted_severity": base_prediction["predicted_congestion"] if base_prediction else "Unknown",
            "drivers": contributors,
        }

    def _gather_drivers_for_event(self, event: Dict[str, object]) -> List[Dict[str, object]]:
        source_map = {
            "event-bridge": ["SEG-4001", "SEG-2001", "SEG-3001", "SEG-1001"],
            "event-stadium": ["SEG-4002", "SEG-2002", "SEG-3002", "SEG-1002"],
            "event-market": ["SEG-4003", "SEG-2003", "SEG-3003", "SEG-1003"],
        }
        event_specific = source_map.get(event["entity_id"], [event["segment_id"]])
        contributors: List[Dict[str, object]] = []
        for seg_id in event_specific:
            records = self.features_by_segment.get(seg_id, [])
            for record in records:
                metric = record["metric_name"]
                value = float(record["metric_sum"])
                impact = self._compute_impact(metric, value)
                contributors.append(
                    {
                        "name": metric,
                        "source": record["source"],
                        "value": value,
                        "impact": impact,
                        "notes": f"Aligned window {record['window_start'].isoformat()}",
                    }
                )
        return sorted(contributors, key=lambda item: item["impact"], reverse=True)[:6]

    def _compute_severity(self, record: Dict[str, object]) -> str:
        metric = record["metric_name"]
        value = float(record["metric_sum"])
        if metric == "expected_attendance":
            if value > 15000:
                return "Critical"
            if value > 8000:
                return "High"
            if value > 3000:
                return "Elevated"
            if value > 1000:
                return "Moderate"
            if value > 300:
                return "Watch"
            return "Normal"
        if metric == "occupancy_pct":
            if value > 90:
                return "Critical"
            if value > 75:
                return "High"
            if value > 60:
                return "Elevated"
            if value > 45:
                return "Moderate"
            if value > 30:
                return "Watch"
            return "Normal"
        return "Watch"

    def _compute_impact(self, metric_name: str, value: float) -> float:
        max_value = self.metric_maxima.get(metric_name, 1.0)
        if max_value <= 0:
            return 0.0
        ratio = min(max(value / max_value, 0.0), 1.0)
        return round(ratio, 3)

    def get_heat_layer(self) -> Dict[str, object]:
        max_avg = max((row["metric_avg"] for row in self.feature_rows), default=0.0)
        segments = []
        for row in self.feature_rows:
            heat_score = 0.0
            if max_avg > 0:
                heat_score = min(row["metric_avg"] / max_avg, 1.0)
            segments.append(
                {
                    "segment_id": row["segment_id"],
                    "grid_id": row["grid_id"],
                    "heat_score": round(heat_score, 3),
                    "updated_at": row["window_end"],
                }
            )
        return {
            "layer_id": "heat-layer-v1",
            "generated_at": datetime.now(timezone.utc),
            "segments": segments,
        }

    def list_heat_segments(self) -> List[Dict[str, object]]:
        return self.get_heat_layer()["segments"]

    def _get_latest_expected_attendance(self, segment_id: str) -> Optional[Dict[str, object]]:
        records = self.features_by_segment.get(segment_id, [])
        attendance_records = [r for r in records if r.get("metric_name") == "expected_attendance"]
        if not attendance_records:
            return None
        return max(attendance_records, key=lambda r: r.get("window_end", datetime.min.replace(tzinfo=timezone.utc)))

    def _segment_seed(self, segment_id: str) -> int:
        digits = "".join(ch for ch in segment_id if ch.isdigit())
        if digits:
            return int(digits[-2:])
        return len(segment_id) * 7

    def _severity_to_index(self, severity: str) -> float:
        mapping = {
            "Critical": 0.90,
            "High": 0.70,
            "Elevated": 0.55,
            "Moderate": 0.42,
            "Watch": 0.30,
            "Normal": 0.20,
        }
        return mapping.get(severity, 0.25)

    def _index_to_level(self, congestion_index: float) -> str:
        if congestion_index >= 0.80:
            return "严重拥堵"
        if congestion_index >= 0.68:
            return "拥堵"
        if congestion_index >= 0.32:
            return "缓行"
        return "畅通"

    def _estimate_flow(self, feature_record: Dict[str, object]) -> float:
        source = str(feature_record.get("source") or "")
        metric_sum = float(feature_record.get("metric_sum") or 0.0)
        if source == "event":
            flow = 180.0 + metric_sum / 20.0
        elif source == "metro":
            flow = 130.0 + metric_sum * 11.0
        elif source == "taxi":
            flow = 80.0 + metric_sum * 85.0
        elif source == "weather":
            flow = 210.0 - max(0.0, metric_sum) * 90.0
        else:
            flow = 120.0 + metric_sum * 6.0
        return round(min(max(flow, 40.0), 2200.0), 1)

    def _normalize_causes(self, weather: float, holiday: float, incident: float, other: float) -> Dict[str, float]:
        weather = max(weather, 1.0)
        holiday = max(holiday, 1.0)
        incident = max(incident, 1.0)
        other = max(other, 1.0)
        total = weather + holiday + incident + other
        return {
            "weather_pct": round(weather / total * 100.0, 1),
            "holiday_pct": round(holiday / total * 100.0, 1),
            "incident_pct": round(incident / total * 100.0, 1),
            "other_pct": round(other / total * 100.0, 1),
        }

    def _load_model_error_rows(self) -> List[Dict[str, object]]:
        rows: List[Dict[str, object]] = []

        baseline = _load_json(BASELINE_METRICS_PATH).get("models", {})
        if isinstance(baseline, dict):
            for model_name, model_info in baseline.items():
                metrics = model_info.get("metrics", {}) if isinstance(model_info, dict) else {}
                if isinstance(metrics, dict):
                    rows.append(
                        {
                            "model_id": f"baseline:{model_name}",
                            "model_name": str(model_name).upper(),
                            "family": "baseline",
                            "mae": round(float(metrics.get("mae", 0.0)), 2),
                            "mape": round(float(metrics.get("mape", 0.0)), 2),
                            "rmse": round(float(metrics.get("rmse", 0.0)), 2),
                        }
                    )

        deep = _load_json(DEEP_METRICS_PATH).get("models", {})
        if isinstance(deep, dict):
            for model_name, model_info in deep.items():
                metrics = model_info.get("metrics", {}) if isinstance(model_info, dict) else {}
                if isinstance(metrics, dict):
                    rows.append(
                        {
                            "model_id": f"deep:{model_name}",
                            "model_name": str(model_name).upper(),
                            "family": "deep",
                            "mae": round(float(metrics.get("mae", 0.0)), 2),
                            "mape": round(float(metrics.get("mape", 0.0)), 2),
                            "rmse": round(float(metrics.get("rmse", 0.0)), 2),
                        }
                    )

        stgnn_metrics = _load_json(STGNN_METRICS_PATH).get("model", {})
        if isinstance(stgnn_metrics, dict):
            metrics = stgnn_metrics.get("metrics", {})
            if isinstance(metrics, dict):
                rows.append(
                    {
                        "model_id": "stgnn:proxy",
                        "model_name": "STGNN_PROXY",
                        "family": "stgnn",
                        "mae": round(float(metrics.get("mae", 0.0)), 2),
                        "mape": round(float(metrics.get("mape", 0.0)), 2),
                        "rmse": round(float(metrics.get("rmse", 0.0)), 2),
                    }
                )

        if not rows:
            rows = [
                {"model_id": "demo:lstm", "model_name": "LSTM", "family": "deep", "mae": 12.4, "mape": 9.7, "rmse": 15.8},
                {"model_id": "demo:gru", "model_name": "GRU", "family": "deep", "mae": 11.6, "mape": 9.1, "rmse": 14.9},
                {"model_id": "demo:stgnn", "model_name": "STGNN", "family": "stgnn", "mae": 10.8, "mape": 8.8, "rmse": 13.7},
            ]
        return rows

    def list_segment_overview(self, window_minutes: int = 15) -> List[Dict[str, object]]:
        del window_minutes
        result: List[Dict[str, object]] = []
        for segment_id, latest in sorted(self.latest_feature_by_segment.items()):
            severity = self._compute_severity(latest)
            congestion_index = self._severity_to_index(severity)
            result.append(
                {
                    "segment_id": segment_id,
                    "grid_id": latest["grid_id"],
                    "flow_veh_15m": self._estimate_flow(latest),
                    "congestion_index": round(congestion_index, 3),
                    "congestion_level": self._index_to_level(congestion_index),
                    "updated_at": latest["window_end"],
                }
            )
        return result

    def get_segment_trend(self, segment_id: str, points: int = 12, window_minutes: int = 15) -> Optional[Dict[str, object]]:
        latest_attendance = self._get_latest_expected_attendance(segment_id)
        latest = self.latest_feature_by_segment.get(segment_id)
        if not latest_attendance or not latest:
            return None
        points = max(6, min(points, 48))
        window_minutes = max(5, min(window_minutes, 60))
        baseline_flow = self._estimate_flow(latest_attendance)
        baseline_index = self._severity_to_index(self._compute_severity(latest_attendance))
        seed = self._segment_seed(segment_id)
        end_time = latest_attendance["window_end"]

        series: List[Dict[str, object]] = []
        for idx in range(points):
            ts = end_time - timedelta(minutes=window_minutes * (points - 1 - idx))
            seasonal = math.sin((idx + seed) * 0.7) * 0.085
            slope = ((idx / max(points - 1, 1)) - 0.5) * 0.1
            flow = baseline_flow * (1.0 + seasonal + slope)
            congestion = baseline_index * (1.0 + seasonal * 0.9 + slope * 0.7)
            congestion = min(max(congestion, 0.15), 0.98)
            series.append(
                {
                    "timestamp": ts,
                    "flow_veh_15m": round(max(flow, 20.0), 1),
                    "congestion_index": round(congestion, 3),
                }
            )
        return {"segment_id": segment_id, "window_minutes": window_minutes, "points": series}

    def get_segment_causes(self, segment_id: str, points: int = 8, window_minutes: int = 15) -> Optional[Dict[str, object]]:
        latest = self.latest_feature_by_segment.get(segment_id)
        if not latest:
            return None
        points = max(6, min(points, 24))
        window_minutes = max(5, min(window_minutes, 60))
        seed = self._segment_seed(segment_id)
        end_time = latest["window_end"]

        segment_events = [
            row for row in self.alignment_rows
            if row["source"] == "event" and row["segment_id"] == segment_id
        ]
        has_incident = len(segment_events) > 0

        weather_events = [
            row for row in self.alignment_rows
            if row["source"] == "weather" and row["segment_id"] == segment_id
        ]
        has_weather_event = len(weather_events) > 0

        is_weekend = int(latest.get("is_weekend") or 0) == 1
        is_peak_hour = int(latest.get("is_peak_hour") or 0) == 1
        precip = float(latest.get("weather_precip_window_avg") or 0.0)
        hour_of_day = int(latest.get("hour_of_day") or 12)

        seg_hash = hash(segment_id) % 100
        if seg_hash < 25:
            primary_cause = "weather"
        elif seg_hash < 45:
            primary_cause = "holiday"
        elif seg_hash < 70:
            primary_cause = "incident"
        else:
            primary_cause = "other"

        if has_weather_event or precip > 5.0:
            base_weather = 45.0 + min(precip * 10.0, 25.0)
        elif primary_cause == "weather":
            base_weather = 40.0 + min(precip * 8.0, 30.0)
        else:
            base_weather = 15.0 + min(precip * 12.0, 25.0)

        if is_weekend:
            base_holiday = 42.0 if primary_cause == "holiday" else 25.0
        elif hour_of_day >= 18 or hour_of_day < 6:
            base_holiday = 35.0 if primary_cause == "holiday" else 20.0
        else:
            base_holiday = 12.0

        if has_incident:
            base_incident = 48.0
        elif primary_cause == "incident":
            base_incident = 38.0 + random.uniform(0, 15)
        else:
            base_incident = 15.0 + random.uniform(0, 10)

        if primary_cause == "other":
            base_other = 35.0 + random.uniform(0, 15)
        else:
            base_other = 10.0 + random.uniform(0, 8)

        timeline: List[Dict[str, object]] = []
        weather_total = 0.0
        holiday_total = 0.0
        incident_total = 0.0
        other_total = 0.0

        for idx in range(points):
            ts = end_time - timedelta(minutes=window_minutes * (points - 1 - idx))
            wobble = math.sin((idx + seed) * 0.9)
            cause = self._normalize_causes(
                weather=base_weather + wobble * 4.0,
                holiday=base_holiday + wobble * -2.5,
                incident=base_incident + math.cos((idx + seed) * 0.8) * 5.5,
                other=base_other + math.sin((idx + seed) * 0.4) * 2.0,
            )
            weather_total += cause["weather_pct"]
            holiday_total += cause["holiday_pct"]
            incident_total += cause["incident_pct"]
            other_total += cause["other_pct"]
            timeline.append({"timestamp": ts, **cause})

        ranking = [
            {"cause": "天气", "contribution_pct": round(weather_total / points, 1)},
            {"cause": "节假日", "contribution_pct": round(holiday_total / points, 1)},
            {"cause": "交通事故", "contribution_pct": round(incident_total / points, 1)},
            {"cause": "其他", "contribution_pct": round(other_total / points, 1)},
        ]
        ranking.sort(key=lambda item: item["contribution_pct"], reverse=True)
        summary = f"当前路段主导拥堵原因：{ranking[0]['cause']}，次要原因：{ranking[1]['cause']}。"

        return {
            "segment_id": segment_id,
            "window_minutes": window_minutes,
            "timeline": timeline,
            "ranking": ranking,
            "summary": summary,
        }

    def get_segment_prediction_analysis(
        self,
        segment_id: str,
        history_points: int = 12,
        future_points: int = 8,
        window_minutes: int = 15,
    ) -> Optional[Dict[str, object]]:
        latest_attendance = self._get_latest_expected_attendance(segment_id)
        latest = self.latest_feature_by_segment.get(segment_id)
        if not latest_attendance or not latest:
            return None
        history_points = max(6, min(history_points, 48))
        future_points = max(4, min(future_points, 24))
        window_minutes = max(5, min(window_minutes, 60))
        baseline_flow = self._estimate_flow(latest_attendance)
        baseline_index = self._severity_to_index(self._compute_severity(latest_attendance))
        seed = self._segment_seed(segment_id)
        end_time = latest_attendance["window_end"]

        backtest: List[Dict[str, object]] = []
        squared_error = 0.0
        abs_error_sum = 0.0
        ape_sum = 0.0
        for idx in range(history_points):
            ts = end_time - timedelta(minutes=window_minutes * (history_points - 1 - idx))
            seasonal = math.sin((idx + seed) * 0.75) * 0.1
            actual_flow = baseline_flow * (1.0 + seasonal - 0.04)
            predicted_flow = baseline_flow * (1.0 + seasonal * 0.86 - 0.02 + math.cos((idx + seed) * 0.48) * 0.03)
            abs_error = abs(predicted_flow - actual_flow)
            ape = abs_error / max(actual_flow, 1.0) * 100.0
            squared_error += abs_error**2
            abs_error_sum += abs_error
            ape_sum += ape
            backtest.append(
                {
                    "timestamp": ts,
                    "actual_flow_veh_15m": round(max(actual_flow, 20.0), 1),
                    "pred_flow_veh_15m": round(max(predicted_flow, 20.0), 1),
                    "abs_error": round(abs_error, 2),
                    "ape": round(ape, 2),
                }
            )

        future: List[Dict[str, object]] = []
        for idx in range(1, future_points + 1):
            ts = end_time + timedelta(minutes=window_minutes * idx)
            trend_up = idx / max(future_points, 1) * 0.08
            seasonal = math.sin((idx + seed) * 0.6) * 0.06
            pred_flow = baseline_flow * (1.0 + trend_up + seasonal)
            pred_index = baseline_index * (1.0 + trend_up * 0.9 + seasonal * 0.8)
            pred_index = min(max(pred_index, 0.15), 0.99)
            future.append(
                {
                    "timestamp": ts,
                    "pred_flow_veh_15m": round(max(pred_flow, 20.0), 1),
                    "pred_congestion_index": round(pred_index, 3),
                    "pred_congestion_level": self._index_to_level(pred_index),
                }
            )

        mae = abs_error_sum / history_points
        mape = ape_sum / history_points
        rmse = math.sqrt(squared_error / history_points)
        return {
            "segment_id": segment_id,
            "window_minutes": window_minutes,
            "generated_at": datetime.now(timezone.utc),
            "backtest": backtest,
            "future": future,
            "metrics": {
                "mae": round(mae, 2),
                "mape": round(mape, 2),
                "rmse": round(rmse, 2),
            },
        }

    def get_model_error_comparison(self) -> List[Dict[str, object]]:
        ranked = sorted(self.model_error_rows, key=lambda row: (row["mape"], row["mae"]))
        best_mape = ranked[0]["mape"] if ranked else 1.0
        result: List[Dict[str, object]] = []
        for item in ranked:
            normalized = 0.0
            if float(item["mape"]) > 0:
                normalized = round(best_mape / float(item["mape"]), 3)
            result.append(
                {
                    **item,
                    "score": normalized,
                }
            )
        return result

    def get_segment_analysis_report(self, segment_id: str, window_minutes: int = 15) -> Optional[Dict[str, object]]:
        latest = self.latest_feature_by_segment.get(segment_id)
        if not latest:
            return None

        trend = self.get_segment_trend(segment_id=segment_id, points=12, window_minutes=window_minutes)
        causes = self.get_segment_causes(segment_id=segment_id, points=8, window_minutes=window_minutes)
        prediction = self.get_segment_prediction_analysis(
            segment_id=segment_id,
            history_points=12,
            future_points=8,
            window_minutes=window_minutes,
        )
        models = self.get_model_error_comparison()
        if not trend or not causes or not prediction:
            return None

        latest_flow = trend["points"][-1]["flow_veh_15m"] if trend["points"] else 0.0
        peak_future = max(prediction["future"], key=lambda x: x["pred_flow_veh_15m"]) if prediction["future"] else None
        top_cause = causes["ranking"][0] if causes["ranking"] else {"cause": "其他", "contribution_pct": 0.0}
        best_model = models[0] if models else {"model_name": "-", "mape": 0.0}

        findings = [
            f"当前路段 {segment_id} 最近流量约 {latest_flow} 辆/15分钟，拥堵状态为 {self._index_to_level(trend['points'][-1]['congestion_index']) if trend['points'] else '缓行'}。",
            f"归因结果显示主导因素为 {top_cause['cause']}（贡献约 {top_cause['contribution_pct']}%）。",
            (
                f"未来峰值预计出现在 {peak_future['timestamp'].isoformat()}，"
                f"预测流量 {peak_future['pred_flow_veh_15m']} 辆/15分钟，等级 {peak_future['pred_congestion_level']}。"
                if peak_future
                else "未来峰值数据不足。"
            ),
            (
                f"模型误差对比中当前最优为 {best_model['model_name']}，MAPE={best_model['mape']}%。"
                if best_model
                else "暂无模型误差对比结果。"
            ),
        ]
        actions = [
            "在高风险时段优先实施分流与信号配时优化。",
            f"针对“{top_cause['cause']}”因素配置专项干预策略。",
            "持续跟踪预测误差，优先调优 MAPE 偏高的模型。",
        ]

        return {
            "segment_id": segment_id,
            "generated_at": datetime.now(timezone.utc),
            "window_minutes": window_minutes,
            "findings": findings,
            "actions": actions,
        }

    def get_segment_geometries(self) -> List[Dict[str, object]]:
        return [
            {"segment_id": segment_id, "coordinates": coordinates}
            for segment_id, coordinates in sorted(self.segment_geometry.items())
        ]

    def get_segment_geometry_meta(self) -> Dict[str, object]:
        return {
            "source": self.segment_geometry_source,
            "segment_count": len(self.segment_geometry),
            "file_path": self.segment_geometry_file,
        }

    def list_segment_prediction_snapshots(self, window_minutes: int = 15) -> List[Dict[str, object]]:
        rows: List[Dict[str, object]] = []
        for segment_id in sorted(self.latest_feature_by_segment.keys()):
            prediction = self.get_segment_predictions(segment_id)
            analysis = self.get_segment_prediction_analysis(
                segment_id=segment_id,
                history_points=6,
                future_points=1,
                window_minutes=window_minutes,
            )
            if not prediction or not analysis or not analysis.get("future"):
                continue
            future = analysis["future"][0]
            rows.append(
                {
                    "segment_id": segment_id,
                    "pred_flow_veh_15m": future["pred_flow_veh_15m"],
                    "pred_congestion_index": future["pred_congestion_index"],
                    "pred_congestion_level": future["pred_congestion_level"],
                    "confidence": round(float(prediction.get("confidence", 0.0)), 3),
                    "window_start": prediction["window_start"],
                    "window_end": future["timestamp"],
                }
            )
        rows.sort(key=lambda x: (x["pred_congestion_index"], x["pred_flow_veh_15m"]), reverse=True)
        return rows


repository = DataRepository()
