"""Declarative base and reusable column helpers."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import Enum
from typing import Any

import sqlalchemy as sa
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


def utcnow() -> datetime:
    """Timezone-aware "now"; kept in one place so tests can freeze it if needed."""
    return datetime.now(UTC)


def enum_column(enum_cls: type[Enum], **kwargs: Any) -> sa.Enum:
    """Store enums by their *value* as a portable VARCHAR + CHECK constraint."""
    return sa.Enum(
        enum_cls,
        native_enum=False,
        validate_strings=True,
        values_callable=lambda members: [member.value for member in members],
        **kwargs,
    )


class Base(DeclarativeBase):
    pass


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), default=utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False
    )
