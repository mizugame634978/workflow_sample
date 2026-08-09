"""Workflow template administration."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import func, select

from app.api.deps import AdminUser, CurrentUser, DbSession
from app.api.serializers import template_detail, template_summary
from app.models import ApproverType, TemplateStep, User, WorkflowTemplate
from app.schemas.common import ItemList
from app.schemas.template import (
    TemplateCreate,
    TemplateDetail,
    TemplateStepIn,
    TemplateSummary,
    TemplateUpdate,
)

router = APIRouter(prefix="/templates", tags=["templates"])


@router.get("", response_model=ItemList[TemplateSummary], summary="申請フォーム一覧")
def list_templates(
    user: CurrentUser,
    db: DbSession,
    include_inactive: bool = Query(False, description="停止中のフォームも含める"),
) -> ItemList[TemplateSummary]:
    query = select(WorkflowTemplate).where(
        WorkflowTemplate.organization_id == user.organization_id
    )
    if not include_inactive:
        query = query.where(WorkflowTemplate.is_active.is_(True))
    templates = db.scalars(query.order_by(WorkflowTemplate.category, WorkflowTemplate.name)).all()
    return ItemList[TemplateSummary](items=[template_summary(t) for t in templates])


@router.get("/{template_id}", response_model=TemplateDetail, summary="申請フォーム詳細")
def get_template(template_id: int, user: CurrentUser, db: DbSession) -> TemplateDetail:
    return template_detail(_load(db, template_id, user))


@router.post(
    "", response_model=TemplateDetail, status_code=status.HTTP_201_CREATED, summary="フォーム作成"
)
def create_template(payload: TemplateCreate, admin: AdminUser, db: DbSession) -> TemplateDetail:
    _assert_route_is_valid(db, admin, payload.steps)
    duplicate = db.scalars(
        select(WorkflowTemplate).where(
            WorkflowTemplate.organization_id == admin.organization_id,
            func.upper(WorkflowTemplate.code) == payload.code.upper(),
        )
    ).first()
    if duplicate is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="このコードのフォームは既に存在します"
        )

    template = WorkflowTemplate(
        organization_id=admin.organization_id,
        code=payload.code.upper(),
        name=payload.name,
        description=payload.description,
        category=payload.category,
        icon=payload.icon,
        form_fields=[field.model_dump(mode="json") for field in payload.form_fields],
        created_by_id=admin.id,
    )
    _replace_steps(template, payload.steps)
    db.add(template)
    db.commit()
    db.refresh(template)
    return template_detail(template)


@router.patch("/{template_id}", response_model=TemplateDetail, summary="フォーム更新")
def update_template(
    template_id: int, payload: TemplateUpdate, admin: AdminUser, db: DbSession
) -> TemplateDetail:
    template = _load(db, template_id, admin)

    for field in ("name", "description", "category", "icon", "is_active"):
        value = getattr(payload, field)
        if value is not None:
            setattr(template, field, value)
    if payload.form_fields is not None:
        template.form_fields = [field.model_dump(mode="json") for field in payload.form_fields]
    if payload.steps is not None:
        _assert_route_is_valid(db, admin, payload.steps)
        _replace_steps(template, payload.steps)

    db.commit()
    db.refresh(template)
    return template_detail(template)


def _load(db: DbSession, template_id: int, user: User) -> WorkflowTemplate:
    template = db.get(WorkflowTemplate, template_id)
    if template is None or template.organization_id != user.organization_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="申請フォームが見つかりません"
        )
    return template


def _assert_route_is_valid(db: DbSession, admin: User, steps: list[TemplateStepIn]) -> None:
    if not steps:
        raise HTTPException(
            status_code=422,
            detail="承認ルートを1ステップ以上設定してください",
        )
    for step in steps:
        if step.approver_type is ApproverType.USER:
            approver = db.get(User, step.approver_user_id) if step.approver_user_id else None
            if approver is None or approver.organization_id != admin.organization_id:
                raise HTTPException(
                    status_code=422,
                    detail=f"ステップ「{step.name}」の承認者が正しくありません",
                )
        if step.approver_type is ApproverType.ROLE and step.approver_role is None:
            raise HTTPException(
                status_code=422,
                detail=f"ステップ「{step.name}」の承認権限を選択してください",
            )


def _replace_steps(template: WorkflowTemplate, steps: list[TemplateStepIn]) -> None:
    template.steps.clear()
    for index, step in enumerate(steps):
        template.steps.append(
            TemplateStep(
                order_index=index,
                name=step.name,
                approver_type=step.approver_type,
                approver_user_id=step.approver_user_id
                if step.approver_type is ApproverType.USER
                else None,
                approver_role=step.approver_role
                if step.approver_type is ApproverType.ROLE
                else None,
            )
        )
