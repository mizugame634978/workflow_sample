"""Shared schema primitives."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Annotated, Generic, TypeVar

from pydantic import BaseModel, BeforeValidator, ConfigDict


def _as_utc(value: datetime | None) -> datetime | None:
    """SQLite hands back naive datetimes; we always persist UTC, so label them."""
    if isinstance(value, datetime) and value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value


UTCDateTime = Annotated[datetime, BeforeValidator(_as_utc)]


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


ItemT = TypeVar("ItemT")


class Page(BaseModel, Generic[ItemT]):
    items: list[ItemT]
    total: int
    page: int
    per_page: int
    pages: int


class ItemList(BaseModel, Generic[ItemT]):
    items: list[ItemT]


class ErrorResponse(BaseModel):
    message: str
    errors: dict[str, str] = {}
