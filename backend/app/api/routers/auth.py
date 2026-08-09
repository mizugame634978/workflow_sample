"""Authentication endpoints."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import func, select

from app.api.deps import CurrentUser, DbSession
from app.core.config import settings
from app.core.security import create_access_token, verify_password
from app.models import User
from app.schemas.identity import LoginRequest, LoginResponse, UserProfile

router = APIRouter(prefix="/auth", tags=["auth"])

_INVALID_CREDENTIALS = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="メールアドレスまたはパスワードが正しくありません",
    headers={"WWW-Authenticate": "Bearer"},
)


@router.post("/login", response_model=LoginResponse, summary="ログイン")
def login(payload: LoginRequest, db: DbSession) -> LoginResponse:
    user = db.scalars(
        select(User).where(func.lower(User.email) == payload.email.lower())
    ).first()
    # Always run the KDF so response time does not leak whether the account exists.
    reference = user.password_hash if user else "pbkdf2_sha256$1$x$x"
    if not verify_password(payload.password, reference) or user is None or not user.is_active:
        raise _INVALID_CREDENTIALS

    token = create_access_token(user.id, {"org": user.organization_id, "role": user.role.value})
    return LoginResponse(
        access_token=token,
        expires_in=settings.access_token_expire_minutes * 60,
        user=UserProfile.model_validate(user),
    )


@router.get("/me", response_model=UserProfile, summary="ログイン中のユーザー")
def me(user: CurrentUser) -> UserProfile:
    return UserProfile.model_validate(user)
