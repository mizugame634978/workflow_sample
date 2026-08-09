"""Dashboard aggregates.

The rollups are computed in Python rather than in SQL: the data volume per
tenant is small, and it keeps the queries portable across SQLite/PostgreSQL.
"""

from __future__ import annotations

from collections import Counter
from datetime import UTC, datetime

from fastapi import APIRouter
from sqlalchemy import func, select

from app.api.deps import CurrentUser, DbSession
from app.models import Request, RequestStatus, User, WorkflowTemplate
from app.schemas.misc import AnalyticsSummary, MonthlyPoint, TemplateUsage
from app.services.request_query import awaiting_action_of

router = APIRouter(prefix="/analytics", tags=["analytics"])

_MONTHS = 6


@router.get("/summary", response_model=AnalyticsSummary, summary="ダッシュボード集計")
def summary(user: CurrentUser, db: DbSession) -> AnalyticsSummary:
    rows = db.execute(_scope_select(user)).all()

    by_status = {status.value: 0 for status in RequestStatus}
    lead_times: list[float] = []
    months: Counter[str] = Counter()
    templates: Counter[str] = Counter()

    for status_value, created_at, submitted_at, completed_at, template_name in rows:
        by_status[status_value.value] += 1
        months[_month_key(created_at)] += 1
        templates[template_name] += 1
        if status_value is RequestStatus.APPROVED and submitted_at and completed_at:
            lead_times.append((_utc(completed_at) - _utc(submitted_at)).total_seconds() / 3600)

    my_open = db.scalar(
        select(func.count(Request.id)).where(
            Request.applicant_id == user.id,
            Request.status.in_([RequestStatus.DRAFT, RequestStatus.PENDING]),
        )
    )
    awaiting = db.scalar(
        select(func.count(Request.id)).where(
            Request.organization_id == user.organization_id, awaiting_action_of(user)
        )
    )

    return AnalyticsSummary(
        by_status=by_status,
        my_open_requests=my_open or 0,
        awaiting_my_approval=awaiting or 0,
        total_requests=len(rows),
        average_lead_time_hours=round(sum(lead_times) / len(lead_times), 1) if lead_times else 0.0,
        monthly=[MonthlyPoint(month=key, count=months.get(key, 0)) for key in _recent_months()],
        by_template=[
            TemplateUsage(name=name, count=count) for name, count in templates.most_common(5)
        ],
    )


def _scope_select(user: User):
    """Admins see the whole tenant; members see the requests they raised."""
    query = (
        select(
            Request.status,
            Request.created_at,
            Request.submitted_at,
            Request.completed_at,
            WorkflowTemplate.name,
        )
        .join(WorkflowTemplate, WorkflowTemplate.id == Request.template_id)
        .where(Request.organization_id == user.organization_id)
    )
    if not user.is_admin:
        query = query.where(Request.applicant_id == user.id)
    return query


def _recent_months(today: datetime | None = None) -> list[str]:
    now = today or datetime.now(UTC)
    year, month = now.year, now.month
    keys: list[str] = []
    for offset in range(_MONTHS - 1, -1, -1):
        total = year * 12 + (month - 1) - offset
        keys.append(f"{total // 12:04d}-{total % 12 + 1:02d}")
    return keys


def _month_key(value: datetime) -> str:
    return f"{value.year:04d}-{value.month:02d}"


def _utc(value: datetime) -> datetime:
    return value.replace(tzinfo=UTC) if value.tzinfo is None else value
