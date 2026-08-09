"""Notification and analytics schemas."""

from __future__ import annotations

from pydantic import BaseModel

from app.models.enums import NotificationType, RequestStatus
from app.schemas.common import ORMModel, UTCDateTime


class NotificationRequestRef(ORMModel):
    id: int
    request_number: str
    title: str
    status: RequestStatus


class NotificationOut(ORMModel):
    id: int
    type: NotificationType
    message: str
    is_read: bool
    created_at: UTCDateTime
    request: NotificationRequestRef


class NotificationList(BaseModel):
    items: list[NotificationOut]
    unread_count: int


class MonthlyPoint(BaseModel):
    month: str
    count: int


class TemplateUsage(BaseModel):
    name: str
    count: int


class AnalyticsSummary(BaseModel):
    by_status: dict[str, int]
    my_open_requests: int
    awaiting_my_approval: int
    total_requests: int
    average_lead_time_hours: float
    monthly: list[MonthlyPoint]
    by_template: list[TemplateUsage]
