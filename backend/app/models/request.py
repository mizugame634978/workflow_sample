"""Request (申請) instances, their approval steps and the surrounding activity trail."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, enum_column, utcnow
from app.models.enums import (
    AuditAction,
    NotificationType,
    RequestStatus,
    StepStatus,
    UserRole,
)

if TYPE_CHECKING:
    from app.models.organization import User
    from app.models.workflow import WorkflowTemplate


class Request(Base, TimestampMixin):
    __tablename__ = "requests"
    __table_args__ = (
        sa.UniqueConstraint("organization_id", "request_number", name="uq_request_org_number"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    organization_id: Mapped[int] = mapped_column(
        sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    template_id: Mapped[int] = mapped_column(
        sa.ForeignKey("workflow_templates.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    applicant_id: Mapped[int] = mapped_column(
        sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    request_number: Mapped[str] = mapped_column(sa.String(24), nullable=False, index=True)
    title: Mapped[str] = mapped_column(sa.String(200), nullable=False)
    form_data: Mapped[dict[str, Any]] = mapped_column(sa.JSON, nullable=False, default=dict)
    status: Mapped[RequestStatus] = mapped_column(
        enum_column(RequestStatus), nullable=False, default=RequestStatus.DRAFT, index=True
    )
    current_step_index: Mapped[int] = mapped_column(sa.Integer, nullable=False, default=0)
    round_no: Mapped[int] = mapped_column(sa.Integer, nullable=False, default=0)
    last_send_back_comment: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    submitted_at: Mapped[datetime | None] = mapped_column(sa.DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(sa.DateTime(timezone=True), nullable=True)

    template: Mapped[WorkflowTemplate] = relationship(lazy="joined")
    applicant: Mapped[User] = relationship(foreign_keys=[applicant_id], lazy="joined")
    steps: Mapped[list["RequestStep"]] = relationship(
        back_populates="request",
        cascade="all, delete-orphan",
        order_by="RequestStep.order_index",
    )
    comments: Mapped[list["Comment"]] = relationship(
        back_populates="request", cascade="all, delete-orphan", order_by="Comment.id"
    )

    @property
    def current_step(self) -> "RequestStep | None":
        if self.status is not RequestStatus.PENDING:
            return None
        for step in self.steps:
            if step.order_index == self.current_step_index:
                return step
        return None


class RequestStep(Base):
    """A materialised approval node: who has to act, and what they decided."""

    __tablename__ = "request_steps"

    id: Mapped[int] = mapped_column(primary_key=True)
    request_id: Mapped[int] = mapped_column(
        sa.ForeignKey("requests.id", ondelete="CASCADE"), nullable=False, index=True
    )
    order_index: Mapped[int] = mapped_column(sa.Integer, nullable=False)
    name: Mapped[str] = mapped_column(sa.String(80), nullable=False)
    approver_id: Mapped[int | None] = mapped_column(
        sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    approver_role: Mapped[UserRole | None] = mapped_column(enum_column(UserRole), nullable=True)
    status: Mapped[StepStatus] = mapped_column(
        enum_column(StepStatus), nullable=False, default=StepStatus.WAITING
    )
    comment: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    acted_by_id: Mapped[int | None] = mapped_column(
        sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    acted_at: Mapped[datetime | None] = mapped_column(sa.DateTime(timezone=True), nullable=True)

    request: Mapped[Request] = relationship(back_populates="steps")
    approver: Mapped[User | None] = relationship(foreign_keys=[approver_id], lazy="joined")
    acted_by: Mapped[User | None] = relationship(foreign_keys=[acted_by_id], lazy="joined")


class Comment(Base):
    __tablename__ = "comments"

    id: Mapped[int] = mapped_column(primary_key=True)
    request_id: Mapped[int] = mapped_column(
        sa.ForeignKey("requests.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[int] = mapped_column(sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    body: Mapped[str] = mapped_column(sa.Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), default=utcnow, nullable=False
    )

    request: Mapped[Request] = relationship(back_populates="comments")
    user: Mapped[User] = relationship(lazy="joined")


class AuditLog(Base):
    """Append-only trail. Never updated, never deleted."""

    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    organization_id: Mapped[int] = mapped_column(
        sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    request_id: Mapped[int] = mapped_column(
        sa.ForeignKey("requests.id", ondelete="CASCADE"), nullable=False, index=True
    )
    actor_id: Mapped[int | None] = mapped_column(
        sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    action: Mapped[AuditAction] = mapped_column(enum_column(AuditAction), nullable=False)
    from_status: Mapped[RequestStatus | None] = mapped_column(
        enum_column(RequestStatus), nullable=True
    )
    to_status: Mapped[RequestStatus | None] = mapped_column(enum_column(RequestStatus), nullable=True)
    step_name: Mapped[str | None] = mapped_column(sa.String(80), nullable=True)
    comment: Mapped[str | None] = mapped_column(sa.Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), default=utcnow, nullable=False
    )

    actor: Mapped[User | None] = relationship(lazy="joined")


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    request_id: Mapped[int] = mapped_column(
        sa.ForeignKey("requests.id", ondelete="CASCADE"), nullable=False, index=True
    )
    type: Mapped[NotificationType] = mapped_column(enum_column(NotificationType), nullable=False)
    message: Mapped[str] = mapped_column(sa.String(255), nullable=False)
    is_read: Mapped[bool] = mapped_column(sa.Boolean, nullable=False, default=False, index=True)
    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), default=utcnow, nullable=False
    )

    request: Mapped[Request] = relationship(lazy="joined")
