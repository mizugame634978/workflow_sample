"""シナリオ: 法人（テナント）間の分離。

同じデータベースを複数の法人が共有していても、業務データは互いに見えない。
このファイルは 1シナリオ内で 2 法人を作り、双方向に確認する。
"""

from __future__ import annotations

import pytest

from tests.scenarios.world import ApiError

pytestmark = pytest.mark.scenario


@pytest.fixture()
def two_companies(tenants):
    """取引のない2つの法人。同じフォームコード・同じ件名をあえて使う。"""
    return tenants.create("あかつき工業"), tenants.create("みなと物産")


def test_申請番号は法人ごとに独立して採番される(two_companies):
    akatsuki, minato = two_companies
    akatsuki_form, minato_form = akatsuki.leave_template(), minato.leave_template()

    akatsuki_first = akatsuki.employee.file_request(akatsuki_form, "休暇", start_date="2026-09-01")
    minato_first = minato.employee.file_request(minato_form, "休暇", start_date="2026-09-01")
    akatsuki_second = akatsuki.colleague.file_request(akatsuki_form, "休暇", start_date="2026-09-02")

    # どちらの法人も 1 番から始まり、他方の採番に影響されない
    assert akatsuki_first["request_number"].endswith("000001")
    assert minato_first["request_number"].endswith("000001")
    assert akatsuki_second["request_number"].endswith("000002")


def test_他法人の申請は閲覧も承認もできない(two_companies):
    akatsuki, minato = two_companies
    request = akatsuki.employee.file_request(
        akatsuki.leave_template(), "社外秘の申請", start_date="2026-09-01"
    )

    # 相手法人の管理者であっても、存在自体が見えない（404）
    for intruder in (minato.admin, minato.manager, minato.ceo):
        with pytest.raises(ApiError) as read:
            intruder.open_request(request)
        assert read.value.status == 404

    with pytest.raises(ApiError) as approval:
        minato.admin.approve(request)
    assert approval.value.status == 404

    # 正当な承認者はこれまでどおり処理できる
    assert akatsuki.manager.approve(request)["status"] == "approved"


def test_他法人のフォームは見えず利用もできない(two_companies):
    akatsuki, minato = two_companies
    akatsuki_form = akatsuki.leave_template()
    minato.expense_template()

    assert [item["name"] for item in minato.employee.available_templates()] == ["経費精算申請"]

    with pytest.raises(ApiError) as error:
        minato.employee.file_request(akatsuki_form, "他社フォームでの申請", start_date="2026-09-01")
    assert error.value.status == 404


def test_同じコードのフォームを両社が持てる(two_companies):
    akatsuki, minato = two_companies

    akatsuki_form = akatsuki.leave_template()
    minato_form = minato.leave_template()

    assert akatsuki_form["code"] == minato_form["code"] == "LEAVE"
    assert akatsuki_form["id"] != minato_form["id"]


def test_集計と通知は法人をまたがない(two_companies):
    akatsuki, minato = two_companies
    akatsuki_form, minato_form = akatsuki.leave_template(), minato.leave_template()

    akatsuki.employee.file_request(akatsuki_form, "あかつきの申請1", start_date="2026-09-01")
    akatsuki.colleague.file_request(akatsuki_form, "あかつきの申請2", start_date="2026-09-02")
    minato.employee.file_request(minato_form, "みなとの申請", start_date="2026-09-01")

    # 管理者の全件表示でも、自社の申請しか出てこない
    assert len(akatsuki.admin.all_requests()) == 2
    assert [item["title"] for item in minato.admin.all_requests()] == ["みなとの申請"]

    # 承認待ちの通知も自社分だけ
    assert akatsuki.manager.notifications()["unread_count"] == 2
    assert minato.manager.notifications()["unread_count"] == 1
    assert len(akatsuki.manager.inbox()) == 2
    assert len(minato.manager.inbox()) == 1

    # ダッシュボードの集計も分離されている
    assert akatsuki.admin.dashboard()["by_status"]["pending"] == 2
    assert minato.admin.dashboard()["by_status"]["pending"] == 1


def test_他のシナリオが作ったデータは一切見えない(tenant):
    """このシナリオ専用の法人からは、共有データベース上の他のデータが観測できない。"""
    leave = tenant.leave_template()
    tenant.employee.file_request(leave, "このシナリオだけの申請", start_date="2026-09-01")

    assert [item["title"] for item in tenant.admin.all_requests()] == ["このシナリオだけの申請"]
    assert len(tenant.admin.colleagues()) == 8  # 既定の登場人物のみ
    assert [item["code"] for item in tenant.admin.available_templates()] == ["LEAVE"]
