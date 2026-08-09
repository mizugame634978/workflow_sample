"""The approval workflow state machine.

This module is the single source of truth for *what may happen* to a request.
Every mutation goes through one of the public functions below, which keeps the
audit trail, the notification fan-out and the permission rules impossible to
bypass from the API layer.

State machine
-------------
    DRAFT --submit--> PENDING --approve(last step)--> APPROVED
                        |  \\--reject--------------> REJECTED
                        |  \\--send_back-----------> DRAFT (差戻し)
                        \\-----cancel--------------> CANCELLED
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import (
    AuditAction,
    AuditLog,
    Comment,
    Notification,
    NotificationType,
    Request,
    RequestStatus,
    RequestStep,
    StepStatus,
    TemplateStep,
    User,
    UserRole,
    WorkflowTemplate,
    utcnow,
)
from app.models.enums import ApproverType
from app.services.errors import InvalidTransition, PermissionDenied, ValidationFailed
from app.services.form_validation import validate_form

__all__ = [
    "add_comment",
    "approve",
    "cancel",
    "create_draft",
    "is_participant",
    "list_audit_logs",
    "next_request_number",
    "send_back",
    "submit",
    "update_draft",
]


# --------------------------------------------------------------------------- draft


def create_draft(
    db: Session,
    *,
    actor: User,
    template: WorkflowTemplate,
    title: str,
    form_data: dict,
) -> Request:
    _assert_same_tenant(actor, template.organization_id)
    if not title or not title.strip():
        raise ValidationFailed("件名を入力してください", errors={"title": "件名は必須項目です"})

    request = Request(
        organization_id=actor.organization_id,
        template_id=template.id,
        applicant_id=actor.id,
        request_number=next_request_number(db, actor.organization_id),
        title=title.strip(),
        form_data=form_data or {},
        status=RequestStatus.DRAFT,
        current_step_index=0,
        round_no=0,
    )
    db.add(request)
    db.flush()
    _log(db, request, actor, AuditAction.CREATED, to_status=RequestStatus.DRAFT)
    db.commit()
    db.refresh(request)
    return request


def update_draft(
    db: Session,
    *,
    actor: User,
    request: Request,
    title: str | None = None,
    form_data: dict | None = None,
) -> Request:
    _assert_same_tenant(actor, request.organization_id)
    if actor.id != request.applicant_id:
        raise PermissionDenied("下書きを編集できるのは申請者本人だけです")
    if request.status is not RequestStatus.DRAFT:
        raise InvalidTransition("申請中または完了済みの申請は編集できません")

    if title is not None:
        if not title.strip():
            raise ValidationFailed("件名を入力してください", errors={"title": "件名は必須項目です"})
        request.title = title.strip()
    if form_data is not None:
        request.form_data = form_data

    _log(db, request, actor, AuditAction.UPDATED)
    db.commit()
    db.refresh(request)
    return request


# ---------------------------------------------------------------------- submission


def submit(db: Session, *, actor: User, request: Request) -> Request:
    _assert_same_tenant(actor, request.organization_id)
    if actor.id != request.applicant_id:
        raise PermissionDenied("申請できるのは申請者本人だけです")
    if request.status is not RequestStatus.DRAFT:
        raise InvalidTransition("この申請はすでに提出されています")

    template = request.template
    if not template.is_active:
        raise ValidationFailed("この申請フォームは現在利用できません")
    if not template.steps:
        raise ValidationFailed("承認ルートが設定されていないため申請できません")

    errors = validate_form(template.form_fields, request.form_data or {})
    if errors:
        raise ValidationFailed(
            "入力内容に誤りがあります: " + ", ".join(sorted(errors)), errors=errors
        )

    request.steps.clear()
    db.flush()
    for definition in template.steps:
        approver_id, approver_role = _resolve_approver(db, definition, request.applicant)
        request.steps.append(
            RequestStep(
                order_index=definition.order_index,
                name=definition.name,
                approver_id=approver_id,
                approver_role=approver_role,
                status=StepStatus.WAITING,
            )
        )

    request.status = RequestStatus.PENDING
    request.current_step_index = 0
    request.round_no += 1
    request.submitted_at = utcnow()
    request.completed_at = None
    db.flush()

    _log(
        db,
        request,
        actor,
        AuditAction.SUBMITTED,
        from_status=RequestStatus.DRAFT,
        to_status=RequestStatus.PENDING,
    )
    _activate_current_step(db, request)
    if request.status is RequestStatus.APPROVED:
        _log(
            db,
            request,
            None,
            AuditAction.APPROVED,
            from_status=RequestStatus.PENDING,
            to_status=RequestStatus.APPROVED,
            comment="承認者が申請者本人のため自動承認されました",
        )
    db.commit()
    db.refresh(request)
    return request


# ------------------------------------------------------------------------- actions


def approve(db: Session, *, actor: User, request: Request, comment: str = "") -> Request:
    step = _authorise_action(actor, request)

    step.status = StepStatus.APPROVED
    step.comment = (comment or "").strip() or None
    step.acted_by_id = actor.id
    step.acted_at = utcnow()
    request.current_step_index += 1
    db.flush()

    _log(
        db,
        request,
        actor,
        AuditAction.APPROVED,
        from_status=RequestStatus.PENDING,
        to_status=RequestStatus.PENDING,
        step_name=step.name,
        comment=step.comment,
    )
    _notify(
        db,
        user_id=request.applicant_id,
        request=request,
        type=NotificationType.STEP_APPROVED,
        message=f"「{request.title}」が{actor.name}さんに承認されました",
    )
    _activate_current_step(db, request)
    if request.status is RequestStatus.APPROVED:
        log = _latest_log(db, request)
        log.to_status = RequestStatus.APPROVED

    db.commit()
    db.refresh(request)
    return request


def reject(db: Session, *, actor: User, request: Request, comment: str) -> Request:
    step = _authorise_action(actor, request)
    body = (comment or "").strip()
    if not body:
        raise ValidationFailed(
            "却下理由を入力してください", errors={"comment": "却下理由は必須です"}
        )

    step.status = StepStatus.REJECTED
    step.comment = body
    step.acted_by_id = actor.id
    step.acted_at = utcnow()
    for remaining in request.steps:
        if remaining.status is StepStatus.WAITING:
            remaining.status = StepStatus.SKIPPED

    request.status = RequestStatus.REJECTED
    request.completed_at = utcnow()
    db.flush()

    _log(
        db,
        request,
        actor,
        AuditAction.REJECTED,
        from_status=RequestStatus.PENDING,
        to_status=RequestStatus.REJECTED,
        step_name=step.name,
        comment=body,
    )
    _notify(
        db,
        user_id=request.applicant_id,
        request=request,
        type=NotificationType.REJECTED,
        message=f"「{request.title}」が{actor.name}さんに却下されました",
    )
    db.commit()
    db.refresh(request)
    return request


def send_back(db: Session, *, actor: User, request: Request, comment: str) -> Request:
    """差戻し — hand the request back to the applicant for correction."""
    step = _authorise_action(actor, request)
    body = (comment or "").strip()
    if not body:
        raise ValidationFailed(
            "差戻し理由を入力してください", errors={"comment": "差戻し理由は必須です"}
        )

    step.status = StepStatus.SENT_BACK
    step.comment = body
    step.acted_by_id = actor.id
    step.acted_at = utcnow()

    request.status = RequestStatus.DRAFT
    request.current_step_index = 0
    request.submitted_at = None
    request.last_send_back_comment = body
    db.flush()

    _log(
        db,
        request,
        actor,
        AuditAction.SENT_BACK,
        from_status=RequestStatus.PENDING,
        to_status=RequestStatus.DRAFT,
        step_name=step.name,
        comment=body,
    )
    _notify(
        db,
        user_id=request.applicant_id,
        request=request,
        type=NotificationType.SENT_BACK,
        message=f"「{request.title}」が{actor.name}さんから差し戻されました",
    )
    db.commit()
    db.refresh(request)
    return request


def cancel(db: Session, *, actor: User, request: Request) -> Request:
    _assert_same_tenant(actor, request.organization_id)
    if actor.id != request.applicant_id:
        raise PermissionDenied("取り下げできるのは申請者本人だけです")
    if request.status not in {RequestStatus.DRAFT, RequestStatus.PENDING}:
        raise InvalidTransition("完了した申請は取り下げできません")

    previous = request.status
    for step in request.steps:
        if step.status in {StepStatus.WAITING, StepStatus.PENDING}:
            step.status = StepStatus.SKIPPED
    request.status = RequestStatus.CANCELLED
    request.completed_at = utcnow()
    db.flush()

    _log(
        db,
        request,
        actor,
        AuditAction.CANCELLED,
        from_status=previous,
        to_status=RequestStatus.CANCELLED,
    )
    db.commit()
    db.refresh(request)
    return request


def add_comment(db: Session, *, actor: User, request: Request, body: str) -> Comment:
    _assert_same_tenant(actor, request.organization_id)
    if not is_participant(actor, request):
        raise PermissionDenied("この申請にコメントする権限がありません")
    text = (body or "").strip()
    if not text:
        raise ValidationFailed("コメントを入力してください", errors={"body": "コメントは必須です"})

    comment = Comment(request_id=request.id, user_id=actor.id, body=text)
    db.add(comment)
    db.flush()
    _log(db, request, actor, AuditAction.COMMENTED, comment=text)

    for user_id in _notification_targets(request, exclude=actor.id):
        _notify(
            db,
            user_id=user_id,
            request=request,
            type=NotificationType.COMMENTED,
            message=f"「{request.title}」に{actor.name}さんがコメントしました",
        )
    db.commit()
    db.refresh(comment)
    return comment


# --------------------------------------------------------------------------- reads


def list_audit_logs(db: Session, request: Request) -> list[AuditLog]:
    return list(
        db.scalars(
            select(AuditLog).where(AuditLog.request_id == request.id).order_by(AuditLog.id)
        ).all()
    )


def is_participant(user: User, request: Request) -> bool:
    if user.organization_id != request.organization_id:
        return False
    if user.id == request.applicant_id or user.is_admin:
        return True
    for step in request.steps:
        if step.approver_id == user.id or step.acted_by_id == user.id:
            return True
        if step.approver_role is not None and user.role is step.approver_role:
            return True
    return False


def can_act_on(user: User, request: Request) -> bool:
    """True when ``user`` is allowed to approve/reject/send back right now."""
    step = request.current_step
    return step is not None and _may_act_on_step(user, step, request)


def next_request_number(db: Session, organization_id: int, *, now: datetime | None = None) -> str:
    year = (now or utcnow()).year
    prefix = f"REQ-{year}-"
    highest = db.scalar(
        select(func.max(Request.request_number)).where(
            Request.organization_id == organization_id,
            Request.request_number.startswith(prefix),
        )
    )
    sequence = int(highest.removeprefix(prefix)) + 1 if highest else 1
    return f"{prefix}{sequence:06d}"


# ------------------------------------------------------------------------ internals


def _authorise_action(actor: User, request: Request) -> RequestStep:
    _assert_same_tenant(actor, request.organization_id)
    if request.status is not RequestStatus.PENDING:
        raise InvalidTransition("承認待ちの申請ではありません")
    step = request.current_step
    if step is None:
        raise InvalidTransition("処理対象の承認ステップがありません")
    if not _may_act_on_step(actor, step, request):
        raise PermissionDenied("この承認ステップを処理する権限がありません")
    return step


def _may_act_on_step(user: User, step: RequestStep, request: Request) -> bool:
    if user.organization_id != request.organization_id or not user.is_active:
        return False
    if user.id == request.applicant_id:
        return False  # 自己承認は許可しない
    if step.approver_id is not None:
        return step.approver_id == user.id
    return step.approver_role is not None and user.role is step.approver_role


def _resolve_approver(
    db: Session, definition: TemplateStep, applicant: User
) -> tuple[int | None, UserRole | None]:
    if definition.approver_type is ApproverType.USER:
        if definition.approver_user_id is None:
            raise ValidationFailed(f"承認ステップ「{definition.name}」に承認者が未設定です")
        return definition.approver_user_id, None

    if definition.approver_type is ApproverType.MANAGER:
        if applicant.manager_id is None:
            raise ValidationFailed(
                f"承認ステップ「{definition.name}」の上長が登録されていません。"
                "管理者に上長の設定を依頼してください"
            )
        return applicant.manager_id, None

    role = definition.approver_role or UserRole.ADMIN
    holders = db.scalar(
        select(func.count(User.id)).where(
            User.organization_id == applicant.organization_id,
            User.role == role,
            User.is_active.is_(True),
        )
    )
    if not holders:
        raise ValidationFailed(f"承認ステップ「{definition.name}」を処理できる担当者がいません")
    return None, role


def _activate_current_step(db: Session, request: Request) -> None:
    """Move to the next actionable step, skipping self-approvals; complete if none left."""
    steps = sorted(request.steps, key=lambda s: s.order_index)
    while request.current_step_index < len(steps):
        step = steps[request.current_step_index]
        if step.approver_id is not None and step.approver_id == request.applicant_id:
            step.status = StepStatus.SKIPPED
            step.comment = "申請者本人のため自動承認"
            step.acted_at = utcnow()
            request.current_step_index += 1
            continue
        step.status = StepStatus.PENDING
        db.flush()
        _notify_approvers(db, request, step)
        return

    request.status = RequestStatus.APPROVED
    request.completed_at = utcnow()
    db.flush()
    _notify(
        db,
        user_id=request.applicant_id,
        request=request,
        type=NotificationType.COMPLETED,
        message=f"「{request.title}」がすべての承認を得て承認されました",
    )


def _notify_approvers(db: Session, request: Request, step: RequestStep) -> None:
    message = (
        f"{request.applicant.name}さんの「{request.title}」があなたの承認を待っています"
    )
    if step.approver_id is not None:
        _notify(
            db,
            user_id=step.approver_id,
            request=request,
            type=NotificationType.APPROVAL_REQUESTED,
            message=message,
        )
        return

    holders = db.scalars(
        select(User.id).where(
            User.organization_id == request.organization_id,
            User.role == step.approver_role,
            User.is_active.is_(True),
            User.id != request.applicant_id,
        )
    ).all()
    for user_id in holders:
        _notify(
            db,
            user_id=user_id,
            request=request,
            type=NotificationType.APPROVAL_REQUESTED,
            message=message,
        )


def _notification_targets(request: Request, *, exclude: int) -> list[int]:
    targets: list[int] = [request.applicant_id]
    step = request.current_step
    if step is not None and step.approver_id is not None:
        targets.append(step.approver_id)
    return [user_id for user_id in dict.fromkeys(targets) if user_id != exclude]


def _notify(
    db: Session, *, user_id: int, request: Request, type: NotificationType, message: str
) -> None:
    db.add(Notification(user_id=user_id, request_id=request.id, type=type, message=message))
    db.flush()


def _log(
    db: Session,
    request: Request,
    actor: User | None,
    action: AuditAction,
    *,
    from_status: RequestStatus | None = None,
    to_status: RequestStatus | None = None,
    step_name: str | None = None,
    comment: str | None = None,
) -> AuditLog:
    entry = AuditLog(
        organization_id=request.organization_id,
        request_id=request.id,
        actor_id=actor.id if actor else None,
        action=action,
        from_status=from_status,
        to_status=to_status,
        step_name=step_name,
        comment=comment,
    )
    db.add(entry)
    db.flush()
    return entry


def _latest_log(db: Session, request: Request) -> AuditLog:
    return db.scalars(
        select(AuditLog)
        .where(AuditLog.request_id == request.id)
        .order_by(AuditLog.id.desc())
        .limit(1)
    ).one()


def _assert_same_tenant(actor: User, organization_id: int) -> None:
    if actor.organization_id != organization_id:
        raise PermissionDenied("他組織のデータにはアクセスできません")
