"""Domain level exceptions.

The API layer maps these onto HTTP status codes in one place, so services never
need to know they are being called over HTTP.
"""

from __future__ import annotations


class WorkflowError(Exception):
    """Base class for every business rule violation."""

    status_code = 400

    def __init__(self, message: str, *, errors: dict[str, str] | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.errors = errors or {}


class PermissionDenied(WorkflowError):
    status_code = 403


class InvalidTransition(WorkflowError):
    status_code = 409


class ValidationFailed(WorkflowError):
    status_code = 422


class NotFound(WorkflowError):
    status_code = 404
