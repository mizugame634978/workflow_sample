"""Translation from ORM objects to API payloads."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.models import Request, RequestStatus, User, UserRole, WorkflowTemplate
from app.schemas.request import RequestDetail, RequestPermissions, RequestSummary
from app.schemas.template import TemplateDetail, TemplateSummary
from app.services import workflow_service as wf

_ROLE_LABELS = {UserRole.ADMIN: "管理者", UserRole.MEMBER: "一般"}


def request_summary(request: Request) -> RequestSummary:
    return RequestSummary.model_validate(_summary_fields(request))


def request_detail(db: Session, request: Request, viewer: User) -> RequestDetail:
    payload = _summary_fields(request)
    payload.update(
        {
            "form_data": request.form_data or {},
            "current_step_index": request.current_step_index,
            "round_no": request.round_no,
            "last_send_back_comment": request.last_send_back_comment,
            "template": request.template,
            "steps": request.steps,
            "comments": request.comments,
            "timeline": wf.list_audit_logs(db, request),
            "permissions": permissions_for(viewer, request),
        }
    )
    return RequestDetail.model_validate(payload)


def permissions_for(viewer: User, request: Request) -> RequestPermissions:
    is_applicant = viewer.id == request.applicant_id
    is_draft = request.status is RequestStatus.DRAFT
    return RequestPermissions(
        can_edit=is_applicant and is_draft,
        can_submit=is_applicant and is_draft,
        can_approve=wf.can_act_on(viewer, request),
        can_cancel=is_applicant
        and request.status in {RequestStatus.DRAFT, RequestStatus.PENDING},
        can_comment=wf.is_participant(viewer, request),
    )


def template_summary(template: WorkflowTemplate) -> TemplateSummary:
    return TemplateSummary.model_validate(
        {
            "id": template.id,
            "code": template.code,
            "name": template.name,
            "description": template.description,
            "category": template.category,
            "icon": template.icon,
            "is_active": template.is_active,
            "step_count": len(template.steps),
            "created_at": template.created_at,
        }
    )


def template_detail(template: WorkflowTemplate) -> TemplateDetail:
    return TemplateDetail.model_validate(
        {
            **template_summary(template).model_dump(),
            "form_fields": template.form_fields or [],
            "steps": template.steps,
        }
    )


def _summary_fields(request: Request) -> dict:
    step = request.current_step
    return {
        "id": request.id,
        "request_number": request.request_number,
        "title": request.title,
        "status": request.status,
        "template_id": request.template_id,
        "template_name": request.template.name,
        "template_category": request.template.category,
        "applicant": request.applicant,
        "current_step_name": step.name if step else None,
        "current_approver_name": _approver_label(step),
        "created_at": request.created_at,
        "updated_at": request.updated_at,
        "submitted_at": request.submitted_at,
        "completed_at": request.completed_at,
    }


def _approver_label(step) -> str | None:
    if step is None:
        return None
    if step.approver is not None:
        return step.approver.name
    if step.approver_role is not None:
        return f"{_ROLE_LABELS.get(step.approver_role, step.approver_role.value)}権限者"
    return None
