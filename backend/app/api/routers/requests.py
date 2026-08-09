"""Request lifecycle endpoints."""

from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import func, or_, select

from app.api.deps import CurrentUser, DbSession
from app.api.serializers import request_detail, request_summary
from app.models import Request, RequestStatus, User, WorkflowTemplate
from app.schemas.common import Page
from app.schemas.request import (
    ActionRequest,
    CommentCreate,
    CommentOut,
    RequestCreate,
    RequestDetail,
    RequestSummary,
    RequestUpdate,
)
from app.services import workflow_service as wf
from app.services.request_query import scoped_query

router = APIRouter(prefix="/requests", tags=["requests"])

Scope = Literal["mine", "inbox", "all"]


@router.get("", response_model=Page[RequestSummary], summary="申請一覧")
def list_requests(
    user: CurrentUser,
    db: DbSession,
    scope: Scope = "mine",
    status_filter: RequestStatus | None = Query(None, alias="status"),
    q: str | None = Query(None, max_length=100, description="件名・申請番号の部分一致"),
    template_id: int | None = None,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
) -> Page[RequestSummary]:
    if scope == "all" and not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="全件表示は管理者のみ利用できます"
        )

    query = scoped_query(user, scope)
    if status_filter is not None:
        query = query.where(Request.status == status_filter)
    if template_id is not None:
        query = query.where(Request.template_id == template_id)
    if q:
        pattern = f"%{q.strip()}%"
        query = query.where(
            or_(Request.title.like(pattern), Request.request_number.like(pattern))
        )

    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
    rows = db.scalars(
        query.order_by(Request.updated_at.desc(), Request.id.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
    ).unique()

    return Page[RequestSummary](
        items=[request_summary(row) for row in rows],
        total=total,
        page=page,
        per_page=per_page,
        pages=max(1, -(-total // per_page)),
    )


@router.post(
    "", response_model=RequestDetail, status_code=status.HTTP_201_CREATED, summary="申請作成"
)
def create_request(payload: RequestCreate, user: CurrentUser, db: DbSession) -> RequestDetail:
    template = db.get(WorkflowTemplate, payload.template_id)
    if template is None or template.organization_id != user.organization_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="申請フォームが見つかりません"
        )

    request = wf.create_draft(
        db, actor=user, template=template, title=payload.title, form_data=payload.form_data
    )
    if payload.submit:
        wf.submit(db, actor=user, request=request)
    return request_detail(db, request, user)


@router.get("/{request_id}", response_model=RequestDetail, summary="申請詳細")
def get_request(request_id: int, user: CurrentUser, db: DbSession) -> RequestDetail:
    request = _load(db, request_id, user)
    if not wf.is_participant(user, request):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="この申請を閲覧する権限がありません"
        )
    return request_detail(db, request, user)


@router.patch("/{request_id}", response_model=RequestDetail, summary="下書き更新")
def update_request(
    request_id: int, payload: RequestUpdate, user: CurrentUser, db: DbSession
) -> RequestDetail:
    request = _load(db, request_id, user)
    wf.update_draft(
        db, actor=user, request=request, title=payload.title, form_data=payload.form_data
    )
    return request_detail(db, request, user)


@router.post("/{request_id}/submit", response_model=RequestDetail, summary="申請提出")
def submit_request(request_id: int, user: CurrentUser, db: DbSession) -> RequestDetail:
    request = _load(db, request_id, user)
    wf.submit(db, actor=user, request=request)
    return request_detail(db, request, user)


@router.post("/{request_id}/approve", response_model=RequestDetail, summary="承認")
def approve_request(
    request_id: int, user: CurrentUser, db: DbSession, payload: ActionRequest | None = None
) -> RequestDetail:
    request = _load(db, request_id, user)
    wf.approve(db, actor=user, request=request, comment=(payload.comment if payload else ""))
    return request_detail(db, request, user)


@router.post("/{request_id}/reject", response_model=RequestDetail, summary="却下")
def reject_request(
    request_id: int, payload: ActionRequest, user: CurrentUser, db: DbSession
) -> RequestDetail:
    request = _load(db, request_id, user)
    wf.reject(db, actor=user, request=request, comment=payload.comment)
    return request_detail(db, request, user)


@router.post("/{request_id}/send-back", response_model=RequestDetail, summary="差戻し")
def send_back_request(
    request_id: int, payload: ActionRequest, user: CurrentUser, db: DbSession
) -> RequestDetail:
    request = _load(db, request_id, user)
    wf.send_back(db, actor=user, request=request, comment=payload.comment)
    return request_detail(db, request, user)


@router.post("/{request_id}/cancel", response_model=RequestDetail, summary="取り下げ")
def cancel_request(request_id: int, user: CurrentUser, db: DbSession) -> RequestDetail:
    request = _load(db, request_id, user)
    wf.cancel(db, actor=user, request=request)
    return request_detail(db, request, user)


@router.post(
    "/{request_id}/comments",
    response_model=CommentOut,
    status_code=status.HTTP_201_CREATED,
    summary="コメント投稿",
)
def create_comment(
    request_id: int, payload: CommentCreate, user: CurrentUser, db: DbSession
) -> CommentOut:
    request = _load(db, request_id, user)
    comment = wf.add_comment(db, actor=user, request=request, body=payload.body)
    return CommentOut.model_validate(comment)


def _load(db: DbSession, request_id: int, user: User) -> Request:
    request = db.get(Request, request_id)
    if request is None or request.organization_id != user.organization_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="申請が見つかりません")
    return request
