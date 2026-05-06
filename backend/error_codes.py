from __future__ import annotations

from fastapi import status


AUTH_INVALID_CREDENTIALS = "AUTH_INVALID_CREDENTIALS"
AUTH_UNAUTHORIZED = "AUTH_UNAUTHORIZED"
AUTH_FORBIDDEN = "AUTH_FORBIDDEN"
RESOURCE_NOT_FOUND = "RESOURCE_NOT_FOUND"
TASK_SUBMIT_FAILED = "TASK_SUBMIT_FAILED"
TASK_NOT_FOUND = "TASK_NOT_FOUND"
VALIDATION_ERROR = "VALIDATION_ERROR"
INTERNAL_ERROR = "INTERNAL_ERROR"


def default_error_code(status_code: int) -> str:
    if status_code == status.HTTP_401_UNAUTHORIZED:
        return AUTH_UNAUTHORIZED
    if status_code == status.HTTP_403_FORBIDDEN:
        return AUTH_FORBIDDEN
    if status_code == status.HTTP_404_NOT_FOUND:
        return RESOURCE_NOT_FOUND
    if status_code == status.HTTP_422_UNPROCESSABLE_ENTITY:
        return VALIDATION_ERROR
    if status_code >= 500:
        return INTERNAL_ERROR
    return "HTTP_ERROR"

