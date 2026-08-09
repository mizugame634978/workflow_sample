"""Behavioural specification for the approval workflow state machine."""

from __future__ import annotations

import pytest
from sqlalchemy.orm import Session

from app.models import (
    AuditAction,
    Notification,
    Organization,
    RequestStatus,
    StepStatus,
    User,
    UserRole,
)
from app.services import workflow_service as wf
from app.services.errors import InvalidTransition, PermissionDenied, ValidationFailed
from tests.conftest import make_template, make_user


@pytest.fixture()
def two_step_template(db: Session, org: Organization, users: dict[str, User]):
    """課長 -> 部長 の 2 段階承認ルート。"""
    return make_template(
        db,
        org,
        users["admin"],
        steps=[
            {"name": "課長承認", "approver_type": "user", "approver_user_id": users["manager"].id},
            {"name": "部長承認", "approver_type": "user", "approver_user_id": users["director"].id},
        ],
    )


def draft(db, applicant, template, **form):
    return wf.create_draft(
        db,
        actor=applicant,
        template=template,
        title="出張旅費の精算",
        form_data=form or {"amount": 42000, "purpose": "大阪支社との合同レビュー"},
    )


# --------------------------------------------------------------------------- draft


def test_create_draft_starts_in_draft_status(db, users, two_step_template):
    request = draft(db, users["employee"], two_step_template)

    assert request.status is RequestStatus.DRAFT
    assert request.current_step_index == 0
    assert request.steps == []
    assert request.applicant_id == users["employee"].id


def test_request_number_is_sequential_and_unique_per_organization(db, users, two_step_template):
    first = draft(db, users["employee"], two_step_template)
    second = draft(db, users["employee"], two_step_template)

    assert first.request_number != second.request_number
    assert first.request_number.startswith("REQ-")
    assert int(first.request_number.split("-")[-1]) + 1 == int(second.request_number.split("-")[-1])


def test_only_the_applicant_can_edit_a_draft(db, users, two_step_template):
    request = draft(db, users["employee"], two_step_template)

    with pytest.raises(PermissionDenied):
        wf.update_draft(db, actor=users["manager"], request=request, title="乗っ取り")


# ----------------------------------------------------------------------- submission


def test_submit_materialises_the_approval_route(db, users, two_step_template):
    request = draft(db, users["employee"], two_step_template)

    wf.submit(db, actor=users["employee"], request=request)

    assert request.status is RequestStatus.PENDING
    assert request.submitted_at is not None
    assert [s.name for s in request.steps] == ["課長承認", "部長承認"]
    assert request.steps[0].status is StepStatus.PENDING
    assert request.steps[1].status is StepStatus.WAITING
    assert request.steps[0].approver_id == users["manager"].id


def test_submit_rejects_missing_required_fields(db, users, two_step_template):
    request = draft(db, users["employee"], two_step_template, amount=1000)

    with pytest.raises(ValidationFailed) as excinfo:
        wf.submit(db, actor=users["employee"], request=request)

    assert "purpose" in str(excinfo.value)
    assert request.status is RequestStatus.DRAFT


def test_submit_rejects_wrong_field_types(db, users, two_step_template):
    request = draft(db, users["employee"], two_step_template, amount="たくさん", purpose="出張")

    with pytest.raises(ValidationFailed):
        wf.submit(db, actor=users["employee"], request=request)


def test_submit_twice_is_an_invalid_transition(db, users, two_step_template):
    request = draft(db, users["employee"], two_step_template)
    wf.submit(db, actor=users["employee"], request=request)

    with pytest.raises(InvalidTransition):
        wf.submit(db, actor=users["employee"], request=request)


def test_manager_step_resolves_to_the_applicants_manager(db, org, users):
    template = make_template(
        db, org, users["admin"], steps=[{"name": "上長承認", "approver_type": "manager"}]
    )
    request = draft(db, users["employee"], template)

    wf.submit(db, actor=users["employee"], request=request)

    assert request.steps[0].approver_id == users["manager"].id


def test_submit_fails_when_the_applicant_has_no_manager(db, org, users):
    template = make_template(
        db, org, users["admin"], steps=[{"name": "上長承認", "approver_type": "manager"}]
    )
    orphan = make_user(db, org, email="orphan@acme.co.jp", name="無所属 四郎")
    request = wf.create_draft(
        db, actor=orphan, template=template, title="申請", form_data={"amount": 1, "purpose": "x"}
    )

    with pytest.raises(ValidationFailed):
        wf.submit(db, actor=orphan, request=request)


def test_step_whose_approver_is_the_applicant_is_skipped(db, org, users):
    template = make_template(
        db,
        org,
        users["admin"],
        steps=[
            {"name": "課長承認", "approver_type": "user", "approver_user_id": users["manager"].id},
            {"name": "部長承認", "approver_type": "user", "approver_user_id": users["director"].id},
        ],
    )
    request = draft(db, users["manager"], template)

    wf.submit(db, actor=users["manager"], request=request)

    assert request.steps[0].status is StepStatus.SKIPPED
    assert request.steps[1].status is StepStatus.PENDING
    assert request.current_step_index == 1


def test_request_is_auto_approved_when_every_step_is_skipped(db, org, users):
    template = make_template(
        db,
        org,
        users["admin"],
        steps=[{"name": "本人確認", "approver_type": "user", "approver_user_id": users["manager"].id}],
    )
    request = draft(db, users["manager"], template)

    wf.submit(db, actor=users["manager"], request=request)

    assert request.status is RequestStatus.APPROVED
    assert request.completed_at is not None


def test_submit_requires_an_active_template(db, users, two_step_template):
    request = draft(db, users["employee"], two_step_template)
    two_step_template.is_active = False
    db.commit()

    with pytest.raises(ValidationFailed):
        wf.submit(db, actor=users["employee"], request=request)


# ------------------------------------------------------------------------ approval


def test_approving_the_first_step_advances_to_the_next_approver(db, users, two_step_template):
    request = draft(db, users["employee"], two_step_template)
    wf.submit(db, actor=users["employee"], request=request)

    wf.approve(db, actor=users["manager"], request=request, comment="問題ありません")

    assert request.status is RequestStatus.PENDING
    assert request.current_step_index == 1
    assert request.steps[0].status is StepStatus.APPROVED
    assert request.steps[0].comment == "問題ありません"
    assert request.steps[0].acted_at is not None
    assert request.steps[1].status is StepStatus.PENDING


def test_approving_the_final_step_completes_the_request(db, users, two_step_template):
    request = draft(db, users["employee"], two_step_template)
    wf.submit(db, actor=users["employee"], request=request)
    wf.approve(db, actor=users["manager"], request=request)

    wf.approve(db, actor=users["director"], request=request)

    assert request.status is RequestStatus.APPROVED
    assert request.completed_at is not None
    assert all(s.status is StepStatus.APPROVED for s in request.steps)


def test_a_non_current_approver_cannot_approve(db, users, two_step_template):
    request = draft(db, users["employee"], two_step_template)
    wf.submit(db, actor=users["employee"], request=request)

    with pytest.raises(PermissionDenied):
        wf.approve(db, actor=users["director"], request=request)


def test_the_applicant_cannot_approve_their_own_request(db, users, two_step_template):
    request = draft(db, users["employee"], two_step_template)
    wf.submit(db, actor=users["employee"], request=request)

    with pytest.raises(PermissionDenied):
        wf.approve(db, actor=users["employee"], request=request)


def test_role_based_step_can_be_approved_by_any_holder_of_the_role(db, org, users):
    template = make_template(
        db,
        org,
        users["admin"],
        steps=[{"name": "管理部承認", "approver_type": "role", "approver_role": "admin"}],
    )
    second_admin = make_user(
        db, org, email="admin2@acme.co.jp", name="管理 五郎", role=UserRole.ADMIN
    )
    request = draft(db, users["employee"], template)
    wf.submit(db, actor=users["employee"], request=request)

    wf.approve(db, actor=second_admin, request=request)

    assert request.status is RequestStatus.APPROVED
    assert request.steps[0].acted_by_id == second_admin.id


def test_a_member_cannot_approve_a_role_step_they_do_not_hold(db, org, users):
    template = make_template(
        db,
        org,
        users["admin"],
        steps=[{"name": "管理部承認", "approver_type": "role", "approver_role": "admin"}],
    )
    request = draft(db, users["employee"], template)
    wf.submit(db, actor=users["employee"], request=request)

    with pytest.raises(PermissionDenied):
        wf.approve(db, actor=users["director"], request=request)


def test_cannot_approve_a_draft(db, users, two_step_template):
    request = draft(db, users["employee"], two_step_template)

    with pytest.raises(InvalidTransition):
        wf.approve(db, actor=users["manager"], request=request)


# ----------------------------------------------------------------------- rejection


def test_rejection_terminates_the_request_and_skips_remaining_steps(db, users, two_step_template):
    request = draft(db, users["employee"], two_step_template)
    wf.submit(db, actor=users["employee"], request=request)

    wf.reject(db, actor=users["manager"], request=request, comment="根拠資料が不足しています")

    assert request.status is RequestStatus.REJECTED
    assert request.completed_at is not None
    assert request.steps[0].status is StepStatus.REJECTED
    assert request.steps[1].status is StepStatus.SKIPPED


def test_rejection_requires_a_comment(db, users, two_step_template):
    request = draft(db, users["employee"], two_step_template)
    wf.submit(db, actor=users["employee"], request=request)

    with pytest.raises(ValidationFailed):
        wf.reject(db, actor=users["manager"], request=request, comment="   ")


def test_a_rejected_request_cannot_be_approved_afterwards(db, users, two_step_template):
    request = draft(db, users["employee"], two_step_template)
    wf.submit(db, actor=users["employee"], request=request)
    wf.reject(db, actor=users["manager"], request=request, comment="却下")

    with pytest.raises(InvalidTransition):
        wf.approve(db, actor=users["director"], request=request)


# ------------------------------------------------------------------- send back (差戻し)


def test_send_back_returns_the_request_to_the_applicant_as_a_draft(db, users, two_step_template):
    request = draft(db, users["employee"], two_step_template)
    wf.submit(db, actor=users["employee"], request=request)

    wf.send_back(db, actor=users["manager"], request=request, comment="金額の内訳を追記してください")

    assert request.status is RequestStatus.DRAFT
    assert request.current_step_index == 0
    assert request.submitted_at is None
    assert request.last_send_back_comment == "金額の内訳を追記してください"


def test_a_sent_back_request_can_be_corrected_and_resubmitted(db, users, two_step_template):
    request = draft(db, users["employee"], two_step_template)
    wf.submit(db, actor=users["employee"], request=request)
    wf.send_back(db, actor=users["manager"], request=request, comment="内訳を追記してください")

    wf.update_draft(
        db,
        actor=users["employee"],
        request=request,
        form_data={"amount": 42000, "purpose": "大阪支社レビュー（宿泊費 12,000 円を含む）"},
    )
    wf.submit(db, actor=users["employee"], request=request)

    assert request.status is RequestStatus.PENDING
    assert request.round_no == 2
    assert request.steps[0].status is StepStatus.PENDING


def test_send_back_requires_a_comment(db, users, two_step_template):
    request = draft(db, users["employee"], two_step_template)
    wf.submit(db, actor=users["employee"], request=request)

    with pytest.raises(ValidationFailed):
        wf.send_back(db, actor=users["manager"], request=request, comment="")


# ---------------------------------------------------------------- cancel / withdraw


def test_the_applicant_can_cancel_a_pending_request(db, users, two_step_template):
    request = draft(db, users["employee"], two_step_template)
    wf.submit(db, actor=users["employee"], request=request)

    wf.cancel(db, actor=users["employee"], request=request)

    assert request.status is RequestStatus.CANCELLED
    assert request.completed_at is not None


def test_an_approver_cannot_cancel_someone_elses_request(db, users, two_step_template):
    request = draft(db, users["employee"], two_step_template)
    wf.submit(db, actor=users["employee"], request=request)

    with pytest.raises(PermissionDenied):
        wf.cancel(db, actor=users["manager"], request=request)


def test_a_completed_request_cannot_be_cancelled(db, users, two_step_template):
    request = draft(db, users["employee"], two_step_template)
    wf.submit(db, actor=users["employee"], request=request)
    wf.approve(db, actor=users["manager"], request=request)
    wf.approve(db, actor=users["director"], request=request)

    with pytest.raises(InvalidTransition):
        wf.cancel(db, actor=users["employee"], request=request)


# --------------------------------------------------------------------- audit trail


def test_every_transition_is_recorded_in_the_audit_log(db, users, two_step_template):
    request = draft(db, users["employee"], two_step_template)
    wf.submit(db, actor=users["employee"], request=request)
    wf.approve(db, actor=users["manager"], request=request, comment="OK")
    wf.reject(db, actor=users["director"], request=request, comment="予算超過のため")

    actions = [log.action for log in wf.list_audit_logs(db, request)]

    assert actions == [
        AuditAction.CREATED,
        AuditAction.SUBMITTED,
        AuditAction.APPROVED,
        AuditAction.REJECTED,
    ]


def test_audit_log_records_the_actor_and_status_transition(db, users, two_step_template):
    request = draft(db, users["employee"], two_step_template)
    wf.submit(db, actor=users["employee"], request=request)

    entry = wf.list_audit_logs(db, request)[-1]

    assert entry.actor_id == users["employee"].id
    assert entry.from_status is RequestStatus.DRAFT
    assert entry.to_status is RequestStatus.PENDING


# -------------------------------------------------------------------- notifications


def test_submitting_notifies_the_current_approver(db, users, two_step_template):
    request = draft(db, users["employee"], two_step_template)

    wf.submit(db, actor=users["employee"], request=request)

    notifications = db.query(Notification).filter_by(user_id=users["manager"].id).all()
    assert len(notifications) == 1
    assert notifications[0].request_id == request.id
    assert notifications[0].is_read is False


def test_approval_notifies_the_applicant_and_the_next_approver(db, users, two_step_template):
    request = draft(db, users["employee"], two_step_template)
    wf.submit(db, actor=users["employee"], request=request)

    wf.approve(db, actor=users["manager"], request=request)

    assert db.query(Notification).filter_by(user_id=users["director"].id).count() == 1
    assert db.query(Notification).filter_by(user_id=users["employee"].id).count() == 1


def test_final_approval_notifies_the_applicant(db, users, two_step_template):
    request = draft(db, users["employee"], two_step_template)
    wf.submit(db, actor=users["employee"], request=request)
    wf.approve(db, actor=users["manager"], request=request)
    wf.approve(db, actor=users["director"], request=request)

    latest = (
        db.query(Notification)
        .filter_by(user_id=users["employee"].id)
        .order_by(Notification.id.desc())
        .first()
    )
    assert "承認" in latest.message


# ------------------------------------------------------------------------ comments


def test_participants_can_comment_on_a_request(db, users, two_step_template):
    request = draft(db, users["employee"], two_step_template)
    wf.submit(db, actor=users["employee"], request=request)

    comment = wf.add_comment(db, actor=users["manager"], request=request, body="領収書を添付願います")

    assert comment.body == "領収書を添付願います"
    assert comment.user_id == users["manager"].id


def test_an_unrelated_user_cannot_comment(db, org, users, two_step_template):
    outsider = make_user(db, org, email="outsider@acme.co.jp", name="無関係 六郎")
    request = draft(db, users["employee"], two_step_template)
    wf.submit(db, actor=users["employee"], request=request)

    with pytest.raises(PermissionDenied):
        wf.add_comment(db, actor=outsider, request=request, body="こんにちは")


def test_empty_comments_are_rejected(db, users, two_step_template):
    request = draft(db, users["employee"], two_step_template)

    with pytest.raises(ValidationFailed):
        wf.add_comment(db, actor=users["employee"], request=request, body="  ")


# --------------------------------------------------------------- multi tenancy


def test_a_user_from_another_tenant_cannot_act_on_a_request(db, users, two_step_template):
    other_org = Organization(name="Globex", slug="globex")
    db.add(other_org)
    db.commit()
    intruder = make_user(db, other_org, email="spy@globex.co.jp", role=UserRole.ADMIN)
    request = draft(db, users["employee"], two_step_template)
    wf.submit(db, actor=users["employee"], request=request)

    with pytest.raises(PermissionDenied):
        wf.approve(db, actor=intruder, request=request)


def test_a_draft_cannot_be_created_from_another_tenants_template(db, org, users, two_step_template):
    other_org = Organization(name="Globex", slug="globex")
    db.add(other_org)
    db.commit()
    outsider = make_user(db, other_org, email="user@globex.co.jp")

    with pytest.raises(PermissionDenied):
        wf.create_draft(
            db, actor=outsider, template=two_step_template, title="不正", form_data={}
        )
