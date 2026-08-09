"""Workflow template (申請フォーム定義) models."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, enum_column
from app.models.enums import ApproverType, UserRole

if TYPE_CHECKING:
    from app.models.organization import User


class WorkflowTemplate(Base, TimestampMixin):
    """A reusable request form + approval route definition."""

    __tablename__ = "workflow_templates"
    __table_args__ = (
        sa.UniqueConstraint("organization_id", "code", name="uq_template_org_code"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    organization_id: Mapped[int] = mapped_column(
        sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    code: Mapped[str] = mapped_column(sa.String(40), nullable=False)
    name: Mapped[str] = mapped_column(sa.String(120), nullable=False)
    description: Mapped[str] = mapped_column(sa.Text, nullable=False, default="")
    category: Mapped[str] = mapped_column(sa.String(60), nullable=False, default="")
    icon: Mapped[str] = mapped_column(sa.String(40), nullable=False, default="document")
    form_fields: Mapped[list[dict[str, Any]]] = mapped_column(sa.JSON, nullable=False, default=list)
    is_active: Mapped[bool] = mapped_column(sa.Boolean, nullable=False, default=True)
    created_by_id: Mapped[int | None] = mapped_column(
        sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    steps: Mapped[list["TemplateStep"]] = relationship(
        back_populates="template",
        cascade="all, delete-orphan",
        order_by="TemplateStep.order_index",
    )


class TemplateStep(Base):
    """One node of an approval route."""

    __tablename__ = "template_steps"

    id: Mapped[int] = mapped_column(primary_key=True)
    template_id: Mapped[int] = mapped_column(
        sa.ForeignKey("workflow_templates.id", ondelete="CASCADE"), nullable=False, index=True
    )
    order_index: Mapped[int] = mapped_column(sa.Integer, nullable=False)
    name: Mapped[str] = mapped_column(sa.String(80), nullable=False)
    approver_type: Mapped[ApproverType] = mapped_column(enum_column(ApproverType), nullable=False)
    approver_user_id: Mapped[int | None] = mapped_column(
        sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    approver_role: Mapped[UserRole | None] = mapped_column(enum_column(UserRole), nullable=True)

    template: Mapped[WorkflowTemplate] = relationship(back_populates="steps")
    approver_user: Mapped["User | None"] = relationship(
        "User", foreign_keys=[approver_user_id], lazy="joined"
    )

    @property
    def approver(self) -> "User | None":
        """Alias used by the API layer, mirroring ``RequestStep.approver``."""
        return self.approver_user
