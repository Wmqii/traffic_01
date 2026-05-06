from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock
from typing import Any, Dict, List


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class AuditLogger:
    def __init__(self) -> None:
        project_root = Path(__file__).resolve().parent.parent
        self._log_path = project_root / "backend" / "logs" / "audit.log"
        self._lock = Lock()

    @property
    def log_path(self) -> Path:
        return self._log_path

    def append(self, payload: Dict[str, Any]) -> None:
        entry = dict(payload)
        entry.setdefault("event_id", str(uuid.uuid4()))
        entry.setdefault("timestamp", _utc_now().isoformat())
        self._log_path.parent.mkdir(parents=True, exist_ok=True)
        line = json.dumps(entry, ensure_ascii=False)
        with self._lock:
            with self._log_path.open("a", encoding="utf-8") as handle:
                handle.write(line + "\n")

    def log_http_request(
        self,
        request_id: str,
        method: str,
        path: str,
        status_code: int,
        duration_ms: float,
        username: str | None = None,
        role: str | None = None,
        client_ip: str | None = None,
        error_code: str | None = None,
    ) -> None:
        self.append(
            {
                "event_type": "http_request",
                "request_id": request_id,
                "method": method,
                "path": path,
                "status_code": status_code,
                "duration_ms": round(duration_ms, 2),
                "username": username,
                "role": role,
                "client_ip": client_ip,
                "error_code": error_code,
            }
        )

    def tail(self, limit: int = 20) -> List[Dict[str, Any]]:
        if not self._log_path.exists():
            return []
        with self._lock:
            lines = self._log_path.read_text(encoding="utf-8").splitlines()
        result: List[Dict[str, Any]] = []
        for line in lines[-limit:]:
            line = line.strip()
            if not line:
                continue
            try:
                result.append(json.loads(line))
            except json.JSONDecodeError:
                continue
        return result


audit_logger = AuditLogger()

