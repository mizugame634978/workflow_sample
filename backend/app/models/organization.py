"""Tenant and identity models."""

from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, enum_column
from app.models.enums import UserRole


class Organization(Base, TimestampMixin):
    """A tenant. Every other row in the system hangs off exactly one of these."""

    __tablename__ = "organizations"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(sa.String(120), nullable=False)
    slug: Mapped[str] = mapped_column(sa.String(60), nullable=False, unique=True, index=True)

    users: Mapped[list["User"]] = relationship(back_populates="organization")


class User(Base, TimestampMixin):
    __tablename__ = "users"
    __table_args__ = (sa.UniqueConstraint("organization_id", "email", name="uq_users_org_email"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    organization_id: Mapped[int] = mapped_column(
        sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    email: Mapped[str] = mapped_column(sa.String(255), nullable=False, index=True)
    name: Mapped[str] = mapped_column(sa.String(120), nullable=False)
    department: Mapped[str] = mapped_column(sa.String(120), nullable=False, default="")
    job_title: Mapped[str] = mapped_column(sa.String(120), nullable=False, default="")
    role: Mapped[UserRole] = mapped_column(
        enum_column(UserRole), nullable=False, default=UserRole.MEMBER
    )
    password_hash: Mapped[str] = mapped_column(sa.String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(sa.Boolean, nullable=False, default=True)
    manager_id: Mapped[int | None] = mapped_column(
        sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    organization: Mapped[Organization] = relationship(back_populates="users")
    manager: Mapped["User | None"] = relationship(remote_side="User.id")

    @property
    def is_admin(self) -> bool:
        return self.role is UserRole.ADMIN
