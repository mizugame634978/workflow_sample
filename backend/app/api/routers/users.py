"""Organisation directory."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import func, select

from app.api.deps import AdminUser, CurrentUser, DbSession
from app.core.security import hash_password
from app.models import User
from app.schemas.common import ItemList
from app.schemas.identity import UserCreate, UserOut

router = APIRouter(prefix="/users", tags=["users"])


@router.get("", response_model=ItemList[UserOut], summary="社内ユーザー一覧")
def list_users(user: CurrentUser, db: DbSession) -> ItemList[UserOut]:
    members = db.scalars(
        select(User)
        .where(User.organization_id == user.organization_id)
        .order_by(User.department, User.name)
    ).all()
    return ItemList[UserOut](items=[UserOut.model_validate(member) for member in members])


@router.post(
    "", response_model=UserOut, status_code=status.HTTP_201_CREATED, summary="ユーザー登録"
)
def create_user(payload: UserCreate, admin: AdminUser, db: DbSession) -> UserOut:
    duplicate = db.scalars(
        select(User).where(
            User.organization_id == admin.organization_id,
            func.lower(User.email) == payload.email.lower(),
        )
    ).first()
    if duplicate is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="このメールアドレスは登録済みです"
        )

    if payload.manager_id is not None:
        manager = db.get(User, payload.manager_id)
        if manager is None or manager.organization_id != admin.organization_id:
            raise HTTPException(
                status_code=422, detail="上長が見つかりません"
            )

    member = User(
        organization_id=admin.organization_id,
        email=payload.email.lower(),
        name=payload.name,
        department=payload.department,
        job_title=payload.job_title,
        role=payload.role,
        manager_id=payload.manager_id,
        password_hash=hash_password(payload.password),
    )
    db.add(member)
    db.commit()
    db.refresh(member)
    return UserOut.model_validate(member)
