"""Auth, organization and user schemas."""

from __future__ import annotations

from pydantic import BaseModel, EmailStr, Field

from app.models.enums import UserRole
from app.schemas.common import ORMModel


class OrganizationOut(ORMModel):
    id: int
    name: str
    slug: str


class UserRef(ORMModel):
    """Minimal user projection embedded in other payloads."""

    id: int
    name: str
    email: EmailStr
    department: str = ""
    job_title: str = ""


class UserOut(UserRef):
    role: UserRole
    is_active: bool
    manager: UserRef | None = None


class UserProfile(UserOut):
    organization: OrganizationOut


class UserCreate(BaseModel):
    email: EmailStr
    name: str = Field(min_length=1, max_length=120)
    password: str = Field(min_length=8, max_length=128)
    department: str = Field(default="", max_length=120)
    job_title: str = Field(default="", max_length=120)
    role: UserRole = UserRole.MEMBER
    manager_id: int | None = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1)


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserProfile
