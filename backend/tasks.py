from __future__ import annotations

import traceback
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from threading import Lock
from typing import Any, Callable, Dict


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class TaskManager:
    def __init__(self, max_workers: int = 4) -> None:
        self._executor = ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="traffic-task")
        self._tasks: Dict[str, Dict[str, Any]] = {}
        self._lock = Lock()

    def submit(self, task_type: str, fn: Callable[[], Dict[str, Any]]) -> str:
        task_id = str(uuid.uuid4())
        record = {
            "task_id": task_id,
            "task_type": task_type,
            "status": "pending",
            "created_at": _utc_now(),
            "started_at": None,
            "finished_at": None,
            "result": None,
            "error": None,
        }
        with self._lock:
            self._tasks[task_id] = record

        def _run() -> None:
            with self._lock:
                self._tasks[task_id]["status"] = "running"
                self._tasks[task_id]["started_at"] = _utc_now()
            try:
                result = fn()
                with self._lock:
                    self._tasks[task_id]["status"] = "completed"
                    self._tasks[task_id]["result"] = result
            except Exception as exc:  # noqa: BLE001
                with self._lock:
                    self._tasks[task_id]["status"] = "failed"
                    self._tasks[task_id]["error"] = {"message": str(exc), "traceback": traceback.format_exc(limit=3)}
            finally:
                with self._lock:
                    self._tasks[task_id]["finished_at"] = _utc_now()

        self._executor.submit(_run)
        return task_id

    def get(self, task_id: str) -> Dict[str, Any] | None:
        with self._lock:
            item = self._tasks.get(task_id)
            return dict(item) if item else None

    def list_recent(self, limit: int = 20) -> list[Dict[str, Any]]:
        with self._lock:
            items = list(self._tasks.values())
        items.sort(key=lambda x: x["created_at"], reverse=True)
        return [dict(item) for item in items[:limit]]


task_manager = TaskManager()

