"""Workflow template schemas."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field, field_validator

from app.models.enums import ApproverType, FieldType, UserRole
from app.schemas.common import ORMModel, UTCDateTime
from app.schemas.identity import UserRef


class FormField(BaseModel):
    key: str = Field(min_length=1, max_length=40, pattern=r"^[a-zA-Z][a-zA-Z0-9_]*$")
    label: str = Field(min_length=1, max_length=80)
    type: FieldType = FieldType.TEXT
    required: bool = False
    help_text: str = ""
    options: list[str] = []
    placeholder: str = ""
    min: float | None = None
    max: float | None = None
    max_length: int | None = None

    @field_validator("options")
    @classmethod
    def _select_needs_options(cls, value: list[str], info) -> list[str]:
        if info.data.get("type") is FieldType.SELECT and not value:
            raise ValueError("選択肢を1つ以上設定してください")
        return value


class TemplateStepIn(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    approver_type: ApproverType
    approver_user_id: int | None = None
    approver_role: UserRole | None = None


class TemplateStepOut(ORMModel):
    id: int
    order_index: int
    name: str
    approver_type: ApproverType
    approver_role: UserRole | None = None
    approver: UserRef | None = None


class TemplateSummary(ORMModel):
    id: int
    code: str
    name: str
    description: str
    category: str
    icon: str
    is_active: bool
    step_count: int = 0
    created_at: UTCDateTime


class TemplateDetail(TemplateSummary):
    form_fields: list[dict[str, Any]]
    steps: list[TemplateStepOut]


class TemplateCreate(BaseModel):
    code: str = Field(min_length=1, max_length=40, pattern=r"^[A-Z][A-Z0-9_]*$")
    name: str = Field(min_length=1, max_length=120)
    description: str = ""
    category: str = Field(default="", max_length=60)
    icon: str = Field(default="document", max_length=40)
    form_fields: list[FormField] = []
    steps: list[TemplateStepIn] = []


class TemplateUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    description: str | None = None
    category: str | None = None
    icon: str | None = None
    is_active: bool | None = None
    form_fields: list[FormField] | None = None
    steps: list[TemplateStepIn] | None = None
