"""シナリオ: 権限（ロール）で承認者を決めるステップ。

特定の個人ではなく「経理権限を持つ人なら誰でも」処理できるルート。
担当者の休暇や異動で決裁が止まらないようにするための仕組み。
"""

from __future__ import annotations

import pytest

from tests.scenarios.world import ApiError

pytestmark = pytest.mark.scenario


def test_権限を持つ担当者なら誰でも承認できる(tenant):
    expense = tenant.expense_template()
    request = tenant.employee.file_request(
        expense, "経理承認を待つ精算", amount=24000, purpose="研修受講料"
    )
    tenant.manager.approve(request)

    # 経理権限を持つ全員の未処理箱に載る
    for approver in (tenant.finance, tenant.auditor, tenant.admin):
        assert [item["id"] for item in approver.inbox()] == [request["id"]]

    # 先に処理した1人の判断で確定し、他の担当者の箱からは消える
    completed = tenant.auditor.approve(request, comment="経理処理を行いました")
    assert completed["status"] == "approved"
    assert completed["steps"][1]["acted_by"]["name"] == tenant.auditor.name
    assert tenant.finance.inbox() == []
    assert tenant.admin.inbox() == []


def test_権限のない社員は権限ステップを処理できない(tenant):
    expense = tenant.expense_template()
    request = tenant.employee.file_request(
        expense, "権限確認用の精算", amount=5000, purpose="消耗品"
    )
    tenant.manager.approve(request)

    for outsider in (tenant.colleague, tenant.director, tenant.ceo):
        with pytest.raises(ApiError) as error:
            outsider.approve(request)
        assert error.value.status == 403

    assert tenant.employee.open_request(request)["status"] == "pending"


def test_経理担当者は自分の精算を自分では承認できず同僚が処理する(tenant):
    """自己承認の禁止。権限を持っていても申請者本人は決裁できない。"""
    expense = tenant.expense_template()

    # 経理担当（管理者権限）自身が精算を申請する
    request = tenant.finance.file_request(
        expense, "経理担当自身の精算", amount=7600, purpose="部門会議の茶菓代"
    )
    tenant.director.approve(request)  # 経理担当の上長は本部長

    assert request["steps"][1]["approver_role"] == "admin"
    assert tenant.finance.inbox() == []  # 自分の申請は自分の箱に入らない

    with pytest.raises(ApiError) as error:
        tenant.finance.approve(request)
    assert error.value.status == 403

    # 同じ権限を持つ別の担当者なら処理できる
    assert tenant.auditor.approve(request)["status"] == "approved"
