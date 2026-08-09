"""HTTP contract tests. These double as the specification the frontend codes against."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.models import Organization, User, UserRole
from tests.conftest import login, make_template, make_user

API = "/api/v1"


@pytest.fixture()
def template(db, org, users):
    return make_template(
        db,
        org,
        users["admin"],
        steps=[
            {"name": "課長承認", "approver_type": "user", "approver_user_id": users["manager"].id},
            {"name": "部長承認", "approver_type": "user", "approver_user_id": users["director"].id},
        ],
    )


@pytest.fixture()
def employee_auth(client, users):
    return login(client, "employee@acme.co.jp")


@pytest.fixture()
def manager_auth(client, users):
    return login(client, "manager@acme.co.jp")


@pytest.fixture()
def admin_auth(client, users):
    return login(client, "admin@acme.co.jp")


def create_request(client, auth, template, *, submit=True, **form):
    response = client.post(
        f"{API}/requests",
        headers=auth,
        json={
            "template_id": template.id,
            "title": "出張旅費の精算",
            "form_data": form or {"amount": 42000, "purpose": "大阪支社との合同レビュー"},
            "submit": submit,
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


# ----------------------------------------------------------------------------- meta


def test_health_endpoint_reports_ok(client):
    response = client.get("/healthz")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_openapi_schema_is_served(client):
    assert client.get("/openapi.json").status_code == 200


# ----------------------------------------------------------------------------- auth


def test_login_returns_a_token_and_the_profile(client, users):
    response = client.post(
        f"{API}/auth/login", json={"email": "employee@acme.co.jp", "password": "Password123!"}
    )

    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]
    assert body["user"]["email"] == "employee@acme.co.jp"
    assert body["user"]["organization"]["name"] == "Acme Corporation"
    assert "password_hash" not in body["user"]


def test_login_is_case_insensitive_on_the_email(client, users):
    response = client.post(
        f"{API}/auth/login", json={"email": "Employee@Acme.CO.JP", "password": "Password123!"}
    )

    assert response.status_code == 200


def test_login_with_a_wrong_password_is_unauthorised(client, users):
    response = client.post(
        f"{API}/auth/login", json={"email": "employee@acme.co.jp", "password": "nope"}
    )

    assert response.status_code == 401


def test_login_of_a_deactivated_user_is_refused(client, db, users):
    users["employee"].is_active = False
    db.commit()

    response = client.post(
        f"{API}/auth/login", json={"email": "employee@acme.co.jp", "password": "Password123!"}
    )

    assert response.status_code == 401


def test_me_returns_the_authenticated_user(client, employee_auth):
    response = client.get(f"{API}/auth/me", headers=employee_auth)

    assert response.status_code == 200
    assert response.json()["name"] == "社員 三郎"


def test_protected_endpoints_require_a_token(client):
    assert client.get(f"{API}/requests").status_code == 401


def test_a_garbage_token_is_rejected(client):
    response = client.get(f"{API}/requests", headers={"Authorization": "Bearer nonsense"})

    assert response.status_code == 401


# ------------------------------------------------------------------------ templates


def test_templates_are_listed_for_the_current_tenant_only(client, db, employee_auth, template):
    other = Organization(name="Globex", slug="globex")
    db.add(other)
    db.commit()
    other_admin = make_user(db, other, email="admin@globex.co.jp", role=UserRole.ADMIN)
    make_template(db, other, other_admin, code="SECRET", name="他社のフォーム")

    response = client.get(f"{API}/templates", headers=employee_auth)

    assert response.status_code == 200
    names = [item["name"] for item in response.json()["items"]]
    assert names == ["経費精算申請"]


def test_template_detail_exposes_fields_and_route(client, employee_auth, template):
    response = client.get(f"{API}/templates/{template.id}", headers=employee_auth)

    body = response.json()
    assert [field["key"] for field in body["form_fields"]] == ["amount", "purpose"]
    assert [step["name"] for step in body["steps"]] == ["課長承認", "部長承認"]
    assert body["steps"][0]["approver"]["name"] == "課長 次郎"


def test_only_admins_may_create_templates(client, employee_auth):
    response = client.post(
        f"{API}/templates",
        headers=employee_auth,
        json={"code": "X", "name": "勝手なフォーム", "form_fields": [], "steps": []},
    )

    assert response.status_code == 403


def test_an_admin_can_create_a_template(client, admin_auth, users):
    response = client.post(
        f"{API}/templates",
        headers=admin_auth,
        json={
            "code": "LEAVE",
            "name": "休暇申請",
            "description": "有給休暇の申請",
            "category": "人事",
            "form_fields": [
                {"key": "start_date", "label": "開始日", "type": "date", "required": True},
                {"key": "reason", "label": "理由", "type": "textarea", "required": False},
            ],
            "steps": [{"name": "上長承認", "approver_type": "manager"}],
        },
    )

    assert response.status_code == 201, response.text
    body = response.json()
    assert body["code"] == "LEAVE"
    assert body["steps"][0]["approver_type"] == "manager"


def test_duplicate_template_codes_are_rejected(client, admin_auth, template):
    response = client.post(
        f"{API}/templates",
        headers=admin_auth,
        json={
            "code": template.code,
            "name": "重複",
            "form_fields": [],
            "steps": [{"name": "上長承認", "approver_type": "manager"}],
        },
    )

    assert response.status_code == 409


def test_a_template_needs_at_least_one_approval_step(client, admin_auth):
    response = client.post(
        f"{API}/templates",
        headers=admin_auth,
        json={"code": "EMPTY", "name": "空", "form_fields": [], "steps": []},
    )

    assert response.status_code == 422


def test_an_admin_can_deactivate_a_template(client, admin_auth, template):
    response = client.patch(
        f"{API}/templates/{template.id}", headers=admin_auth, json={"is_active": False}
    )

    assert response.status_code == 200
    assert response.json()["is_active"] is False


# ------------------------------------------------------------------------- requests


def test_creating_a_draft_does_not_start_the_route(client, employee_auth, template):
    body = create_request(client, employee_auth, template, submit=False)

    assert body["status"] == "draft"
    assert body["steps"] == []
    assert body["permissions"]["can_edit"] is True


def test_creating_and_submitting_in_one_call(client, employee_auth, template):
    body = create_request(client, employee_auth, template)

    assert body["status"] == "pending"
    assert body["steps"][0]["status"] == "pending"
    assert body["steps"][0]["approver"]["name"] == "課長 次郎"
    assert body["request_number"].startswith("REQ-")


def test_invalid_form_payloads_return_field_errors(client, employee_auth, template):
    response = client.post(
        f"{API}/requests",
        headers=employee_auth,
        json={
            "template_id": template.id,
            "title": "不備のある申請",
            "form_data": {"amount": "たくさん"},
            "submit": True,
        },
    )

    assert response.status_code == 422
    assert set(response.json()["errors"]) == {"amount", "purpose"}


def test_a_draft_can_be_edited_then_submitted(client, employee_auth, template):
    draft = create_request(client, employee_auth, template, submit=False, amount=100)

    patched = client.patch(
        f"{API}/requests/{draft['id']}",
        headers=employee_auth,
        json={"title": "修正後の件名", "form_data": {"amount": 200, "purpose": "打合せ"}},
    )
    assert patched.status_code == 200
    assert patched.json()["title"] == "修正後の件名"

    submitted = client.post(f"{API}/requests/{draft['id']}/submit", headers=employee_auth)
    assert submitted.status_code == 200
    assert submitted.json()["status"] == "pending"


def test_the_inbox_scope_lists_requests_awaiting_the_caller(
    client, employee_auth, manager_auth, template
):
    create_request(client, employee_auth, template)

    inbox = client.get(f"{API}/requests?scope=inbox", headers=manager_auth).json()
    empty = client.get(f"{API}/requests?scope=inbox", headers=employee_auth).json()

    assert inbox["total"] == 1
    assert inbox["items"][0]["current_step_name"] == "課長承認"
    assert empty["total"] == 0


def test_the_mine_scope_lists_only_my_requests(client, employee_auth, manager_auth, template):
    create_request(client, employee_auth, template)

    mine = client.get(f"{API}/requests?scope=mine", headers=employee_auth).json()
    manager_view = client.get(f"{API}/requests?scope=mine", headers=manager_auth).json()

    assert mine["total"] == 1
    assert manager_view["total"] == 0


def test_requests_can_be_filtered_by_status_and_searched(client, employee_auth, template):
    create_request(client, employee_auth, template)
    create_request(client, employee_auth, template, submit=False)

    pending = client.get(f"{API}/requests?scope=mine&status=pending", headers=employee_auth).json()
    hit = client.get(f"{API}/requests?scope=mine&q=出張", headers=employee_auth).json()
    miss = client.get(f"{API}/requests?scope=mine&q=存在しない", headers=employee_auth).json()

    assert pending["total"] == 1
    assert hit["total"] == 2
    assert miss["total"] == 0


def test_request_listing_is_paginated(client, employee_auth, template):
    for _ in range(3):
        create_request(client, employee_auth, template)

    page = client.get(f"{API}/requests?scope=mine&page=2&per_page=2", headers=employee_auth).json()

    assert page["total"] == 3
    assert page["page"] == 2
    assert len(page["items"]) == 1


def test_an_admin_sees_every_request_in_the_tenant(client, employee_auth, admin_auth, template):
    create_request(client, employee_auth, template)

    everything = client.get(f"{API}/requests?scope=all", headers=admin_auth).json()

    assert everything["total"] == 1


def test_a_member_cannot_use_the_all_scope(client, employee_auth, template):
    response = client.get(f"{API}/requests?scope=all", headers=employee_auth)

    assert response.status_code == 403


def test_request_detail_includes_timeline_and_permissions(
    client, employee_auth, manager_auth, template
):
    created = create_request(client, employee_auth, template)

    detail = client.get(f"{API}/requests/{created['id']}", headers=manager_auth).json()

    assert [entry["action"] for entry in detail["timeline"]] == ["created", "submitted"]
    assert detail["timeline"][0]["actor"]["name"] == "社員 三郎"
    assert detail["permissions"] == {
        "can_edit": False,
        "can_submit": False,
        "can_approve": True,
        "can_cancel": False,
        "can_comment": True,
    }
    assert detail["applicant"]["department"] == "Engineering"


def test_an_unrelated_user_cannot_read_a_request(client, db, org, employee_auth, template):
    make_user(db, org, email="outsider@acme.co.jp", name="無関係 六郎")
    created = create_request(client, employee_auth, template)
    outsider_auth = login(client, "outsider@acme.co.jp")

    response = client.get(f"{API}/requests/{created['id']}", headers=outsider_auth)

    assert response.status_code == 403


def test_a_missing_request_returns_404(client, employee_auth):
    assert client.get(f"{API}/requests/9999", headers=employee_auth).status_code == 404


def test_cross_tenant_request_access_returns_404(client, db, employee_auth, template):
    other = Organization(name="Globex", slug="globex")
    db.add(other)
    db.commit()
    make_user(db, other, email="spy@globex.co.jp", role=UserRole.ADMIN)
    created = create_request(client, employee_auth, template)
    spy_auth = login(client, "spy@globex.co.jp")

    response = client.get(f"{API}/requests/{created['id']}", headers=spy_auth)

    assert response.status_code == 404


# -------------------------------------------------------------------------- actions


def test_the_full_approval_journey(client, employee_auth, manager_auth, template):
    created = create_request(client, employee_auth, template)
    director_auth = login(client, "director@acme.co.jp")

    first = client.post(
        f"{API}/requests/{created['id']}/approve", headers=manager_auth, json={"comment": "承認します"}
    )
    assert first.status_code == 200
    assert first.json()["status"] == "pending"

    second = client.post(
        f"{API}/requests/{created['id']}/approve", headers=director_auth, json={}
    )
    assert second.status_code == 200
    body = second.json()
    assert body["status"] == "approved"
    assert body["completed_at"] is not None
    assert [step["status"] for step in body["steps"]] == ["approved", "approved"]


def test_approving_out_of_turn_is_forbidden(client, employee_auth, template):
    created = create_request(client, employee_auth, template)
    director_auth = login(client, "director@acme.co.jp")

    response = client.post(
        f"{API}/requests/{created['id']}/approve", headers=director_auth, json={}
    )

    assert response.status_code == 403


def test_rejecting_requires_a_reason(client, employee_auth, manager_auth, template):
    created = create_request(client, employee_auth, template)

    response = client.post(
        f"{API}/requests/{created['id']}/reject", headers=manager_auth, json={"comment": ""}
    )

    assert response.status_code == 422


def test_rejection_finishes_the_request(client, employee_auth, manager_auth, template):
    created = create_request(client, employee_auth, template)

    response = client.post(
        f"{API}/requests/{created['id']}/reject",
        headers=manager_auth,
        json={"comment": "予算超過のため"},
    )

    assert response.json()["status"] == "rejected"


def test_send_back_returns_the_request_to_draft(client, employee_auth, manager_auth, template):
    created = create_request(client, employee_auth, template)

    response = client.post(
        f"{API}/requests/{created['id']}/send-back",
        headers=manager_auth,
        json={"comment": "内訳を追記してください"},
    )

    body = response.json()
    assert body["status"] == "draft"
    assert body["last_send_back_comment"] == "内訳を追記してください"
    assert body["permissions"]["can_edit"] is False  # 承認者から見た権限


def test_the_applicant_can_cancel(client, employee_auth, template):
    created = create_request(client, employee_auth, template)

    response = client.post(f"{API}/requests/{created['id']}/cancel", headers=employee_auth)

    assert response.json()["status"] == "cancelled"


def test_approving_a_finished_request_is_a_conflict(client, employee_auth, manager_auth, template):
    created = create_request(client, employee_auth, template)
    client.post(f"{API}/requests/{created['id']}/cancel", headers=employee_auth)

    response = client.post(f"{API}/requests/{created['id']}/approve", headers=manager_auth, json={})

    assert response.status_code == 409


def test_comments_are_appended_to_the_thread(client, employee_auth, manager_auth, template):
    created = create_request(client, employee_auth, template)

    posted = client.post(
        f"{API}/requests/{created['id']}/comments",
        headers=manager_auth,
        json={"body": "領収書の添付をお願いします"},
    )
    assert posted.status_code == 201

    detail = client.get(f"{API}/requests/{created['id']}", headers=employee_auth).json()
    assert detail["comments"][0]["body"] == "領収書の添付をお願いします"
    assert detail["comments"][0]["user"]["name"] == "課長 次郎"


# --------------------------------------------------------------------- notifications


def test_the_approver_is_notified_and_can_mark_as_read(
    client, employee_auth, manager_auth, template
):
    create_request(client, employee_auth, template)

    unread = client.get(f"{API}/notifications", headers=manager_auth).json()
    assert unread["unread_count"] == 1
    notification_id = unread["items"][0]["id"]

    client.post(f"{API}/notifications/{notification_id}/read", headers=manager_auth)
    after = client.get(f"{API}/notifications", headers=manager_auth).json()
    assert after["unread_count"] == 0


def test_all_notifications_can_be_marked_read_at_once(
    client, employee_auth, manager_auth, template
):
    create_request(client, employee_auth, template)
    create_request(client, employee_auth, template)

    client.post(f"{API}/notifications/read-all", headers=manager_auth)

    assert client.get(f"{API}/notifications", headers=manager_auth).json()["unread_count"] == 0


def test_notifications_of_other_users_are_not_visible(client, employee_auth, template):
    create_request(client, employee_auth, template)

    mine = client.get(f"{API}/notifications", headers=employee_auth).json()

    assert mine["unread_count"] == 0


# ------------------------------------------------------------------------ analytics


def test_the_dashboard_summary_aggregates_the_tenant(
    client, employee_auth, manager_auth, template
):
    approved = create_request(client, employee_auth, template)
    client.post(f"{API}/requests/{approved['id']}/approve", headers=manager_auth, json={})
    client.post(
        f"{API}/requests/{approved['id']}/approve",
        headers=login(client, "director@acme.co.jp"),
        json={},
    )
    create_request(client, employee_auth, template)
    create_request(client, employee_auth, template, submit=False)

    summary = client.get(f"{API}/analytics/summary", headers=employee_auth).json()

    assert summary["by_status"]["approved"] == 1
    assert summary["by_status"]["pending"] == 1
    assert summary["by_status"]["draft"] == 1
    assert summary["my_open_requests"] == 2
    assert summary["awaiting_my_approval"] == 0
    assert summary["average_lead_time_hours"] >= 0
    assert len(summary["monthly"]) == 6
    assert summary["by_template"][0]["name"] == "経費精算申請"


def test_the_summary_counts_the_approver_inbox(client, employee_auth, manager_auth, template):
    create_request(client, employee_auth, template)

    summary = client.get(f"{API}/analytics/summary", headers=manager_auth).json()

    assert summary["awaiting_my_approval"] == 1


# ---------------------------------------------------------------------------- users


def test_the_user_directory_is_scoped_to_the_tenant(client, db, employee_auth, users):
    other = Organization(name="Globex", slug="globex")
    db.add(other)
    db.commit()
    make_user(db, other, email="ghost@globex.co.jp", name="他社 社員")

    response = client.get(f"{API}/users", headers=employee_auth)

    assert response.status_code == 200
    emails = {item["email"] for item in response.json()["items"]}
    assert "ghost@globex.co.jp" not in emails
    assert "manager@acme.co.jp" in emails


def test_the_directory_exposes_reporting_lines(client, employee_auth, users):
    items = client.get(f"{API}/users", headers=employee_auth).json()["items"]

    employee = next(item for item in items if item["email"] == "employee@acme.co.jp")
    assert employee["manager"]["name"] == "課長 次郎"


def test_only_admins_can_create_users(client: TestClient, employee_auth):
    response = client.post(
        f"{API}/users",
        headers=employee_auth,
        json={"email": "new@acme.co.jp", "name": "新人", "password": "Password123!"},
    )

    assert response.status_code == 403


def test_an_admin_can_invite_a_user(client, admin_auth, users):
    response = client.post(
        f"{API}/users",
        headers=admin_auth,
        json={
            "email": "new@acme.co.jp",
            "name": "新人 七海",
            "password": "Password123!",
            "department": "営業",
            "manager_id": users["manager"].id,
        },
    )

    assert response.status_code == 201
    assert response.json()["manager"]["name"] == "課長 次郎"


def test_duplicate_emails_are_rejected(client, admin_auth, users):
    response = client.post(
        f"{API}/users",
        headers=admin_auth,
        json={"email": "employee@acme.co.jp", "name": "重複", "password": "Password123!"},
    )

    assert response.status_code == 409


def test_users_created_through_the_api_can_log_in(client, admin_auth):
    client.post(
        f"{API}/users",
        headers=admin_auth,
        json={"email": "new@acme.co.jp", "name": "新人 七海", "password": "Password123!"},
    )

    assert login(client, "new@acme.co.jp")


def test_a_user_object_never_leaks_the_password_hash(client, employee_auth):
    payload: User = client.get(f"{API}/users", headers=employee_auth).json()

    assert "password_hash" not in str(payload)
