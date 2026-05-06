from __future__ import annotations

import json
import os
import threading
import time
from dataclasses import dataclass
from typing import Any


def _now_ts() -> float:
    return time.time()


@dataclass
class CacheConfig:
    backend: str
    default_ttl: int
    redis_url: str


class MemoryTTLCache:
    def __init__(self) -> None:
        self._store: dict[str, tuple[float, Any]] = {}
        self._lock = threading.Lock()
        self._hits = 0
        self._misses = 0

    def get(self, key: str) -> Any | None:
        with self._lock:
            item = self._store.get(key)
            if item is None:
                self._misses += 1
                return None
            expire_ts, value = item
            if expire_ts <= _now_ts():
                self._store.pop(key, None)
                self._misses += 1
                return None
            self._hits += 1
            return value

    def set(self, key: str, value: Any, ttl_seconds: int) -> None:
        expire_ts = _now_ts() + max(1, ttl_seconds)
        with self._lock:
            self._store[key] = (expire_ts, value)

    def delete(self, key: str) -> None:
        with self._lock:
            self._store.pop(key, None)

    def stats(self) -> dict[str, Any]:
        with self._lock:
            return {
                "backend": "memory",
                "hits": self._hits,
                "misses": self._misses,
                "keys": len(self._store),
            }


class RedisTTLCache:
    def __init__(self, redis_client: Any) -> None:
        self._redis = redis_client
        self._hits = 0
        self._misses = 0

    def get(self, key: str) -> Any | None:
        raw = self._redis.get(key)
        if raw is None:
            self._misses += 1
            return None
        self._hits += 1
        return json.loads(raw)

    def set(self, key: str, value: Any, ttl_seconds: int) -> None:
        payload = json.dumps(value, ensure_ascii=False, default=str)
        self._redis.setex(key, max(1, ttl_seconds), payload)

    def delete(self, key: str) -> None:
        self._redis.delete(key)

    def stats(self) -> dict[str, Any]:
        return {
            "backend": "redis",
            "hits": self._hits,
            "misses": self._misses,
            "keys": -1,
        }


class CacheService:
    def __init__(self, impl: MemoryTTLCache | RedisTTLCache, config: CacheConfig, fallback_reason: str = "") -> None:
        self._impl = impl
        self.config = config
        self.fallback_reason = fallback_reason

    def get(self, key: str) -> Any | None:
        return self._impl.get(key)

    def set(self, key: str, value: Any, ttl_seconds: int | None = None) -> None:
        ttl = ttl_seconds if ttl_seconds is not None else self.config.default_ttl
        self._impl.set(key, value, ttl)

    def delete(self, key: str) -> None:
        self._impl.delete(key)

    def stats(self) -> dict[str, Any]:
        payload = self._impl.stats()
        payload["configured_backend"] = self.config.backend
        payload["default_ttl_seconds"] = self.config.default_ttl
        payload["fallback_reason"] = self.fallback_reason
        return payload


def build_cache_service() -> CacheService:
    backend = os.getenv("TRAFFIC_CACHE_BACKEND", "auto").strip().lower()
    ttl = int(os.getenv("TRAFFIC_CACHE_TTL_SECONDS", "300"))
    redis_url = os.getenv("TRAFFIC_REDIS_URL", "redis://127.0.0.1:6379/0").strip()
    config = CacheConfig(backend=backend, default_ttl=max(1, ttl), redis_url=redis_url)

    if backend in {"redis", "auto"}:
        try:
            import redis  # type: ignore

            client = redis.Redis.from_url(redis_url, decode_responses=True)
            client.ping()
            return CacheService(RedisTTLCache(client), config)
        except Exception as exc:  # noqa: BLE001
            if backend == "redis":
                return CacheService(MemoryTTLCache(), config, fallback_reason=f"redis_required_but_unavailable: {exc}")
            return CacheService(MemoryTTLCache(), config, fallback_reason=f"redis_unavailable: {exc}")

    return CacheService(MemoryTTLCache(), config)


cache_service = build_cache_service()

