"""Domain enumerations shared by models, services and API schemas."""

from __future__ import annotations

from enum import StrEnum


class UserRole(StrEnum):
    ADMIN = "admin"
    MEMBER = "member"


class RequestStatus(StrEnum):
    DRAFT = "draft"
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELLED = "cancelled"

    @property
    def is_terminal(self) -> bool:
        return self in {RequestStatus.APPROVED, RequestStatus.REJECTED, RequestStatus.CANCELLED}


class StepStatus(StrEnum):
    WAITING = "waiting"
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    SENT_BACK = "sent_back"
    SKIPPED = "skipped"


class ApproverType(StrEnum):
    USER = "user"
    MANAGER = "manager"
    ROLE = "role"


class AuditAction(StrEnum):
    CREATED = "created"
    UPDATED = "updated"
    SUBMITTED = "submitted"
    APPROVED = "approved"
    REJECTED = "rejected"
    SENT_BACK = "sent_back"
    CANCELLED = "cancelled"
    COMMENTED = "commented"


class NotificationType(StrEnum):
    APPROVAL_REQUESTED = "approval_requested"
    STEP_APPROVED = "step_approved"
    COMPLETED = "completed"
    REJECTED = "rejected"
    SENT_BACK = "sent_back"
    COMMENTED = "commented"


class FieldType(StrEnum):
    TEXT = "text"
    TEXTAREA = "textarea"
    NUMBER = "number"
    DATE = "date"
    SELECT = "select"
