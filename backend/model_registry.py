from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock
from typing import Any, Dict, List


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class ModelRegistry:
    def __init__(self) -> None:
        self._project_root = Path(__file__).resolve().parent.parent
        self._metrics_path = self._project_root / "model" / "deep" / "output" / "metrics.json"
        self._registry_path = self._project_root / "model" / "registry" / "model_registry.json"
        self._lock = Lock()

    def _read_json(self, path: Path) -> Dict[str, Any]:
        return json.loads(path.read_text(encoding="utf-8"))

    def _write_json(self, path: Path, value: Dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")

    def _read_metrics_payload(self) -> Dict[str, Any]:
        if not self._metrics_path.exists():
            raise FileNotFoundError(f"Metrics file not found: {self._metrics_path}")
        return self._read_json(self._metrics_path)

    def _extract_family_metrics(self, payload: Dict[str, Any], model_family: str) -> Dict[str, float]:
        models = payload.get("models", {})
        family_obj = models.get(model_family, {})
        metric_obj = family_obj.get("metrics", {})
        return {
            "rmse": float(metric_obj.get("rmse", 0.0)),
            "mae": float(metric_obj.get("mae", 0.0)),
            "mape": float(metric_obj.get("mape", 0.0)),
        }

    def _best_family(self, payload: Dict[str, Any]) -> str:
        best_family = ""
        best_mape = float("inf")
        for family, item in payload.get("models", {}).items():
            mape = float(item.get("metrics", {}).get("mape", float("inf")))
            if mape < best_mape:
                best_mape = mape
                best_family = family
        if best_family:
            return best_family
        return "gru"

    def _bootstrap_state(self) -> Dict[str, Any]:
        payload = self._read_metrics_payload()
        family = self._best_family(payload)
        metrics = self._extract_family_metrics(payload, family)
        created_at = _utc_now().isoformat()
        return {
            "updated_at": created_at,
            "active": {
                "version": f"bootstrap-{family}",
                "model_family": family,
                "published_at": created_at,
                "source": "metrics_bootstrap",
                "metrics": metrics,
            },
            "candidates": [],
            "history": [
                {
                    "event": "bootstrap",
                    "at": created_at,
                    "detail": f"initialize active model from metrics ({family})",
                }
            ],
            "last_health": None,
        }

    def _load_state(self) -> Dict[str, Any]:
        if self._registry_path.exists():
            return self._read_json(self._registry_path)
        state = self._bootstrap_state()
        self._write_json(self._registry_path, state)
        return state

    def _persist(self, state: Dict[str, Any]) -> None:
        state["updated_at"] = _utc_now().isoformat()
        self._write_json(self._registry_path, state)

    def snapshot(self) -> Dict[str, Any]:
        with self._lock:
            return self._load_state()

    def submit_retrain(self, model_family: str = "gru", trigger: str = "manual", dry_run: bool = True) -> Dict[str, Any]:
        with self._lock:
            payload = self._read_metrics_payload()
            available = list(payload.get("models", {}).keys())
            if model_family not in available:
                raise ValueError(f"Unsupported model_family={model_family}, available={available}")

            if not dry_run:
                cmd = [sys.executable, "model/deep/scripts/train_deep_models.py", "--epochs", "5"]
                subprocess.run(cmd, cwd=str(self._project_root), check=True)
                payload = self._read_metrics_payload()

            metrics = self._extract_family_metrics(payload, model_family)
            candidate_version = f"{model_family}-{_utc_now().strftime('%Y%m%d%H%M%S')}"
            candidate = {
                "version": candidate_version,
                "model_family": model_family,
                "trigger": trigger,
                "dry_run": dry_run,
                "created_at": _utc_now().isoformat(),
                "metrics": metrics,
                "metrics_source": str(self._metrics_path.relative_to(self._project_root)).replace("\\", "/"),
            }

            state = self._load_state()
            state.setdefault("candidates", [])
            state.setdefault("history", [])
            state["candidates"].insert(0, candidate)
            state["history"].append(
                {
                    "event": "retrain",
                    "at": _utc_now().isoformat(),
                    "detail": f"candidate={candidate_version}, family={model_family}, dry_run={dry_run}",
                }
            )
            self._persist(state)

            return {
                "task": "model_retrain",
                "candidate_version": candidate_version,
                "model_family": model_family,
                "dry_run": dry_run,
                "metrics": metrics,
            }

    def publish(self, model_version: str | None = None, operator: str = "system") -> Dict[str, Any]:
        with self._lock:
            state = self._load_state()
            candidates: List[Dict[str, Any]] = state.get("candidates", [])
            active = state.get("active", {})

            selected: Dict[str, Any] | None = None
            if model_version:
                selected = next((item for item in candidates if item.get("version") == model_version), None)
                if not selected and active.get("version") == model_version:
                    selected = {
                        "version": active.get("version"),
                        "model_family": active.get("model_family"),
                        "metrics": active.get("metrics", {}),
                    }
            else:
                selected = candidates[0] if candidates else None
                if not selected and active.get("version"):
                    selected = {
                        "version": active.get("version"),
                        "model_family": active.get("model_family"),
                        "metrics": active.get("metrics", {}),
                    }

            if not selected:
                raise ValueError("No publishable model version found")

            published = {
                "version": selected.get("version", ""),
                "model_family": selected.get("model_family", "unknown"),
                "published_at": _utc_now().isoformat(),
                "source": "candidate_publish",
                "metrics": selected.get("metrics", {}),
            }
            state["active"] = published
            state.setdefault("history", [])
            state["history"].append(
                {
                    "event": "publish",
                    "at": _utc_now().isoformat(),
                    "detail": f"version={published['version']}, operator={operator}",
                }
            )
            self._persist(state)

            return {
                "task": "model_publish",
                "active_version": published["version"],
                "model_family": published["model_family"],
                "published_at": published["published_at"],
                "metrics": published["metrics"],
            }

    def rollback(self, target_version: str | None = None, operator: str = "system") -> Dict[str, Any]:
        with self._lock:
            state = self._load_state()
            candidates: List[Dict[str, Any]] = state.get("candidates", [])
            active = state.get("active", {})
            current_version = str(active.get("version", ""))

            selected: Dict[str, Any] | None = None
            if target_version:
                selected = next((item for item in candidates if item.get("version") == target_version), None)
                if not selected and current_version == target_version:
                    selected = {
                        "version": current_version,
                        "model_family": active.get("model_family", "unknown"),
                        "metrics": active.get("metrics", {}),
                    }
            else:
                for item in candidates:
                    version = str(item.get("version", ""))
                    if version and version != current_version:
                        selected = item
                        break

            if not selected:
                raise ValueError("No rollback target available")

            rolled_back = {
                "version": selected.get("version", ""),
                "model_family": selected.get("model_family", "unknown"),
                "published_at": _utc_now().isoformat(),
                "source": "rollback",
                "metrics": selected.get("metrics", {}),
            }
            state["active"] = rolled_back
            state.setdefault("history", [])
            state["history"].append(
                {
                    "event": "rollback",
                    "at": _utc_now().isoformat(),
                    "detail": f"from={current_version}, to={rolled_back['version']}, operator={operator}",
                }
            )
            self._persist(state)

            return {
                "task": "model_rollback",
                "from_version": current_version,
                "active_version": rolled_back["version"],
                "model_family": rolled_back["model_family"],
                "rolled_back_at": rolled_back["published_at"],
            }

    def health_check(self) -> Dict[str, Any]:
        with self._lock:
            state = self._load_state()
            active = state.get("active", {})
            metrics_mtime = None
            metrics_age_hours = None
            metrics_exists = self._metrics_path.exists()
            if metrics_exists:
                metrics_mtime = datetime.fromtimestamp(self._metrics_path.stat().st_mtime, tz=timezone.utc)
                metrics_age_hours = round((_utc_now() - metrics_mtime).total_seconds() / 3600.0, 2)

            mape = active.get("metrics", {}).get("mape")
            mape_ok = mape is None or float(mape) < 1000.0
            freshness_ok = metrics_age_hours is not None and metrics_age_hours <= 72.0
            healthy = bool(active.get("version")) and metrics_exists and freshness_ok and mape_ok

            detail = {
                "status": "healthy" if healthy else "degraded",
                "checked_at": _utc_now().isoformat(),
                "active_version": active.get("version", ""),
                "model_family": active.get("model_family", ""),
                "metrics_exists": metrics_exists,
                "metrics_age_hours": metrics_age_hours,
                "mape": float(mape) if mape is not None else None,
                "thresholds": {"metrics_age_hours_lte": 72.0, "mape_lt": 1000.0},
            }
            state["last_health"] = detail
            state.setdefault("history", [])
            state["history"].append(
                {
                    "event": "health_check",
                    "at": _utc_now().isoformat(),
                    "detail": f"status={detail['status']}, active={detail['active_version']}",
                }
            )
            self._persist(state)
            return detail


model_registry = ModelRegistry()
