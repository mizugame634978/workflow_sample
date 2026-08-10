"""シナリオ: 稟議（課長 → 本部長 → 代表 の3段階決裁）。"""

from __future__ import annotations

import pytest

from tests.scenarios.world import ApiError

pytestmark = pytest.mark.scenario


def test_稟議が3段階の決裁を経て承認される(tenant):
    ringi = tenant.ringi_template()
    request = tenant.employee.file_request(
        ringi,
        "顧客サポート基盤の刷新",
        amount=4800000,
        proposal="SaaS 型のサポート基盤を導入し、初回応答時間を短縮する",
    )

    # 承認は必ず定義された順序で回る
    for approver, expected_next in [
        (tenant.manager, "本部長承認"),
        (tenant.director, "最終決裁"),
    ]:
        assert [item["id"] for item in approver.inbox()] == [request["id"]]
        state = approver.approve(request, comment="承認します")
        assert state["status"] == "pending"
        assert state["current_step_name"] == expected_next

    decided = tenant.ceo.approve(request, comment="実行してください")
    assert decided["status"] == "approved"
    assert [step["status"] for step in decided["steps"]] == ["approved"] * 3
    assert [step["acted_by"]["name"] for step in decided["steps"]] == [
        tenant.manager.name,
        tenant.director.name,
        tenant.ceo.name,
    ]


def test_承認の順序は飛び越せない(tenant):
    ringi = tenant.ringi_template()
    request = tenant.employee.file_request(
        ringi, "新規ツールの導入", amount=300000, proposal="検証環境の整備"
    )

    # まだ課長の番なので、本部長も代表も操作できない
    for actor in (tenant.director, tenant.ceo):
        with pytest.raises(ApiError) as error:
            actor.approve(request)
        assert error.value.status == 403
        assert actor.inbox() == []

    tenant.manager.approve(request)
    assert [item["id"] for item in tenant.director.inbox()] == [request["id"]]


def test_課長本人の稟議では自分の承認ステップが自動でスキップされる(tenant):
    ringi = tenant.ringi_template()

    request = tenant.manager.file_request(
        ringi, "チーム体制の見直し", amount=0, proposal="増員による開発体制の強化"
    )

    assert request["steps"][0]["status"] == "skipped"
    assert request["current_step_name"] == "本部長承認"
    # 自分の申請は自分の未処理箱には入らない
    assert tenant.manager.inbox() == []

    tenant.director.approve(request)
    assert tenant.ceo.approve(request)["status"] == "approved"


def test_ルートに含まれない社員は承認も閲覧もできない(tenant):
    ringi = tenant.ringi_template()
    request = tenant.employee.file_request(
        ringi, "同僚には見えない稟議", amount=1000, proposal="検証用"
    )

    with pytest.raises(ApiError) as approval:
        tenant.colleague.approve(request)
    assert approval.value.status == 403

    with pytest.raises(ApiError) as read:
        tenant.colleague.open_request(request)
    assert read.value.status == 403

    assert tenant.employee.open_request(request)["status"] == "pending"


def test_途中で却下すると残りの決裁者には回らない(tenant):
    ringi = tenant.ringi_template()
    request = tenant.employee.file_request(
        ringi, "予算超過の施策", amount=99000000, proposal="大規模な設備投資"
    )

    tenant.manager.approve(request)
    rejected = tenant.director.reject(request, comment="今期の投資枠を超えています")

    assert rejected["status"] == "rejected"
    assert [step["status"] for step in rejected["steps"]] == ["approved", "rejected", "skipped"]
    assert tenant.ceo.inbox() == []
