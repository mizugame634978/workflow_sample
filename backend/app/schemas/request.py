"""Request (申請) schemas."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from app.models.enums import AuditAction, RequestStatus, StepStatus, UserRole
from app.schemas.common import ORMModel, UTCDateTime
from app.schemas.identity import UserRef


class RequestCreate(BaseModel):
    template_id: int
    title: str = Field(min_length=1, max_length=200)
    form_data: dict[str, Any] = {}
    submit: bool = False


class RequestUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    form_data: dict[str, Any] | None = None


class ActionRequest(BaseModel):
    comment: str = ""


class CommentCreate(BaseModel):
    body: str = Field(min_length=1, max_length=2000)


class CommentOut(ORMModel):
    id: int
    body: str
    created_at: UTCDateTime
    user: UserRef


class StepOut(ORMModel):
    id: int
    order_index: int
    name: str
    status: StepStatus
    approver: UserRef | None = None
    approver_role: UserRole | None = None
    comment: str | None = None
    acted_by: UserRef | None = None
    acted_at: UTCDateTime | None = None


class TimelineEntry(ORMModel):
    id: int
    action: AuditAction
    actor: UserRef | None = None
    from_status: RequestStatus | None = None
    to_status: RequestStatus | None = None
    step_name: str | None = None
    comment: str | None = None
    created_at: UTCDateTime


class RequestPermissions(BaseModel):
    can_edit: bool
    can_submit: bool
    can_approve: bool
    can_cancel: bool
    can_comment: bool


class RequestSummary(ORMModel):
    id: int
    request_number: str
    title: str
    status: RequestStatus
    template_id: int
    template_name: str
    template_category: str
    applicant: UserRef
    current_step_name: str | None = None
    current_approver_name: str | None = None
    created_at: UTCDateTime
    updated_at: UTCDateTime
    submitted_at: UTCDateTime | None = None
    completed_at: UTCDateTime | None = None


class TemplateOfRequest(ORMModel):
    id: int
    code: str
    name: str
    category: str
    description: str
    form_fields: list[dict[str, Any]]


class RequestDetail(RequestSummary):
    form_data: dict[str, Any]
    current_step_index: int
    round_no: int
    last_send_back_comment: str | None = None
    template: TemplateOfRequest
    steps: list[StepOut]
    comments: list[CommentOut]
    timeline: list[TimelineEntry]
    permissions: RequestPermissions
