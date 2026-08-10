"""シナリオ: 管理者による組織・フォームの運用。"""

from __future__ import annotations

import pytest

from tests.scenarios.world import ApiError

pytestmark = pytest.mark.scenario


def test_管理者が登録した新入社員がその日から申請できる(tenant):
    leave = tenant.leave_template()

    newcomer = tenant.hire(
        key="newcomer",
        name="新人 七海",
        department="プロダクト開発部",
        manager=tenant.manager,
    )

    # 登録された本人がログインして申請する
    request = newcomer.file_request(leave, "有給休暇の取得", start_date="2026-09-01")

    assert request["status"] == "pending"
    assert request["applicant"]["name"] == "新人 七海"
    assert request["steps"][0]["approver"]["name"] == tenant.manager.name
    assert [item["id"] for item in tenant.manager.inbox()] == [request["id"]]


def test_上長が未設定の社員は上長承認のフォームに申請できない(tenant):
    leave = tenant.leave_template()
    orphan = tenant.hire(key="orphan", name="無所属 四郎")

    with pytest.raises(ApiError) as error:
        orphan.file_request(leave, "上長がいない申請", start_date="2026-09-01")

    assert error.value.status == 422
    assert "上長" in error.value.message


def test_一般社員は社員を登録できない(tenant):
    with pytest.raises(ApiError) as error:
        tenant.employee.register_user(name="勝手な登録", email=tenant.email_for("intruder"))

    assert error.value.status == 403


def test_同じメールアドレスの社員は二重登録できない(tenant):
    with pytest.raises(ApiError) as error:
        tenant.admin.register_user(name="重複 太郎", email=tenant.employee.email)

    assert error.value.status == 409


def test_フォームを停止すると新規申請できず再開すれば再び申請できる(tenant):
    leave = tenant.leave_template()
    assert "休暇申請" in [item["name"] for item in tenant.employee.available_templates()]

    tenant.admin.revise_template(leave, is_active=False)

    assert "休暇申請" not in [item["name"] for item in tenant.employee.available_templates()]
    with pytest.raises(ApiError) as error:
        tenant.employee.file_request(leave, "停止中のフォームへの申請", start_date="2026-09-01")
    assert error.value.status == 422

    tenant.admin.revise_template(leave, is_active=True)
    assert tenant.employee.file_request(leave, "再開後の申請", start_date="2026-09-01")[
        "status"
    ] == "pending"


def test_フォームの改訂は進行中の申請に影響しない(tenant):
    leave = tenant.leave_template()
    in_flight = tenant.employee.file_request(leave, "改訂前に出した申請", start_date="2026-09-01")

    # 管理者が「理由」を必須項目に変更する
    tenant.admin.revise_template(
        leave,
        form_fields=[
            {"key": "start_date", "label": "開始日", "type": "date", "required": True},
            {"key": "reason", "label": "理由", "type": "text", "required": True},
        ],
    )

    # 改訂後の新規申請では理由が必須になる
    with pytest.raises(ApiError) as error:
        tenant.colleague.file_request(leave, "改訂後の申請", start_date="2026-09-10")
    assert error.value.status == 422
    assert "reason" in error.value.errors

    # 既に承認ルートへ乗っている申請はそのまま完了できる
    assert tenant.manager.approve(in_flight)["status"] == "approved"


def test_管理者は法人全体の申請を横断して確認できる(tenant):
    leave = tenant.leave_template()
    tenant.employee.file_request(leave, "主任の休暇", start_date="2026-09-01")
    tenant.colleague.file_request(leave, "エンジニアの休暇", start_date="2026-09-02")

    titles = sorted(item["title"] for item in tenant.admin.all_requests())
    assert titles == ["エンジニアの休暇", "主任の休暇"]

    # 一般社員には全件表示は許可されない
    with pytest.raises(ApiError) as error:
        tenant.employee.all_requests()
    assert error.value.status == 403
