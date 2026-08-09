"""Reusable, tenant-safe query building for request listings."""

from __future__ import annotations

from sqlalchemy import ColumnElement, Select, and_, or_, select

from app.models import Request, RequestStatus, RequestStep, StepStatus, User


def awaiting_action_of(user: User) -> ColumnElement[bool]:
    """Predicate: the request's *current* step is actionable by ``user``."""
    step_matches = (
        select(RequestStep.id)
        .where(
            RequestStep.request_id == Request.id,
            RequestStep.order_index == Request.current_step_index,
            RequestStep.status == StepStatus.PENDING,
            or_(
                RequestStep.approver_id == user.id,
                RequestStep.approver_role == user.role,
            ),
        )
        .exists()
    )
    return and_(
        Request.status == RequestStatus.PENDING,
        Request.applicant_id != user.id,
        step_matches,
    )


def scoped_query(user: User, scope: str) -> Select:
    """Build the base ``SELECT`` for a listing scope. ``scope`` is pre-validated."""
    query = select(Request).where(Request.organization_id == user.organization_id)
    if scope == "mine":
        return query.where(Request.applicant_id == user.id)
    if scope == "inbox":
        return query.where(awaiting_action_of(user))
    return query  # "all" — admin only, enforced by the router
