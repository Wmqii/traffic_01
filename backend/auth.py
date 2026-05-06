from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from typing import Callable, Dict

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer


JWT_SECRET = os.getenv("TRAFFIC_JWT_SECRET", "traffic-dev-secret-change")
JWT_ALGORITHM = "HS256"
TOKEN_TTL_MINUTES = int(os.getenv("TRAFFIC_JWT_TTL_MINUTES", "60"))


USERS: Dict[str, Dict[str, str]] = {
    "admin": {"password": "admin123", "role": "admin", "display_name": "System Admin"},
    "analyst": {"password": "analyst123", "role": "analyst", "display_name": "Traffic Analyst"},
    "viewer": {"password": "viewer123", "role": "viewer", "display_name": "Read-Only Viewer"},
}

security = HTTPBearer(auto_error=False)


def authenticate_user(username: str, password: str) -> Dict[str, str] | None:
    user = USERS.get(username)
    if not user:
        return None
    if user["password"] != password:
        return None
    return {"username": username, "role": user["role"], "display_name": user["display_name"]}


def create_access_token(username: str, role: str) -> tuple[str, datetime]:
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=TOKEN_TTL_MINUTES)
    payload = {
        "sub": username,
        "role": role,
        "exp": expires_at,
        "iat": datetime.now(timezone.utc),
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return token, expires_at


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> Dict[str, str]:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing bearer token",
        )
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        username = payload.get("sub")
        role = payload.get("role")
        if not username or not role:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload",
            )
        user = USERS.get(username)
        if not user or user["role"] != role:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token user invalid",
            )
        return {"username": username, "role": role, "display_name": user["display_name"]}
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token validation failed",
        )


def require_roles(*roles: str) -> Callable[[Dict[str, str]], Dict[str, str]]:
    allowed = set(roles)

    def dependency(user: Dict[str, str] = Depends(get_current_user)) -> Dict[str, str]:
        if user["role"] not in allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{user['role']}' is not allowed",
            )
        return user

    return dependency

