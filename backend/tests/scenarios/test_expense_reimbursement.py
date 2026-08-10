"""シナリオ: 経費精算（上長承認 → 経理承認）。

登場人物はすべてこのファイル専用の法人に所属するため、
他のシナリオがどんなデータを作っても結果は変わらない。
"""

from __future__ import annotations

import pytest

from tests.scenarios.world import ApiError

pytestmark = pytest.mark.scenario


def test_経費精算が上長と経理の承認を経て完了する(tenant):
    expense = tenant.expense_template()

    # 1. 主任が精算を申請する
    request = tenant.employee.file_request(
        expense, "10月度 交通費精算", amount=18400, purpose="名古屋支社での定例会議"
    )
    assert request["status"] == "pending"
    assert request["current_step_name"] == "上長承認"

    # 2. 上長（課長）の未処理箱に届き、本人以外には届かない
    assert [item["id"] for item in tenant.manager.inbox()] == [request["id"]]
    assert tenant.director.inbox() == []
    assert tenant.manager.notifications()["unread_count"] == 1

    # 3. 上長が承認すると、経理権限を持つ担当者へ回る
    after_manager = tenant.manager.approve(request, comment="内容を確認しました")
    assert after_manager["status"] == "pending"
    assert after_manager["steps"][0]["status"] == "approved"
    assert after_manager["current_step_name"] == "経理承認"
    assert [item["id"] for item in tenant.finance.inbox()] == [request["id"]]

    # 4. 経理が承認して決裁完了
    completed = tenant.finance.approve(request)
    assert completed["status"] == "approved"
    assert completed["completed_at"] is not None
    assert [step["status"] for step in completed["steps"]] == ["approved", "approved"]

    # 5. 申請者には「承認された」通知が届いている
    messages = [item["message"] for item in tenant.employee.notifications()["items"]]
    assert any("承認" in message for message in messages)

    # 6. 監査ログに一連の流れが順番どおり残っている
    actions = [entry["action"] for entry in tenant.employee.open_request(request)["timeline"]]
    assert actions == ["created", "submitted", "approved", "approved"]

    # 7. ダッシュボードにも反映される
    assert tenant.employee.dashboard()["by_status"]["approved"] == 1
    assert tenant.manager.inbox() == []


def test_差し戻された精算を修正して再提出すると承認ルートがやり直しになる(tenant):
    expense = tenant.expense_template()
    request = tenant.employee.file_request(
        expense, "出張旅費の精算", amount=42000, purpose="大阪支社との合同レビュー"
    )

    # 上長が内訳不足を理由に差し戻す
    sent_back = tenant.manager.send_back(request, comment="金額の内訳を利用目的に追記してください")
    assert sent_back["status"] == "draft"
    assert sent_back["last_send_back_comment"] == "金額の内訳を利用目的に追記してください"
    assert tenant.manager.inbox() == []

    # 申請者が修正して再提出する
    tenant.employee.update_draft(request, purpose="大阪支社レビュー（宿泊費 12,000 円を含む）")
    resubmitted = tenant.employee.submit(request)
    assert resubmitted["status"] == "pending"
    assert resubmitted["round_no"] == 2
    assert resubmitted["steps"][0]["status"] == "pending"

    # 再度上長 → 経理と回って完了する
    tenant.manager.approve(request)
    assert tenant.finance.approve(request)["status"] == "approved"


def test_却下された精算はそれ以上処理できない(tenant):
    expense = tenant.expense_template()
    request = tenant.employee.file_request(
        expense, "高額な備品の精算", amount=980000, purpose="個人的な購入"
    )

    rejected = tenant.manager.reject(request, comment="業務との関連が確認できません")
    assert rejected["status"] == "rejected"
    assert rejected["steps"][1]["status"] == "skipped"

    # 後続の承認者が触っても状態は変わらない
    with pytest.raises(ApiError) as error:
        tenant.finance.approve(request)
    assert error.value.status == 409
    assert tenant.employee.open_request(request)["status"] == "rejected"


def test_却下と差戻しには理由の入力が必要(tenant):
    expense = tenant.expense_template()
    request = tenant.employee.file_request(expense, "会議費の精算", amount=8000, purpose="打合せ")

    with pytest.raises(ApiError) as rejection:
        tenant.manager.reject(request, comment="   ")
    assert rejection.value.status == 422

    with pytest.raises(ApiError) as send_back:
        tenant.manager.send_back(request, comment="")
    assert send_back.value.status == 422

    # どちらも失敗しているので、申請は承認待ちのまま
    assert tenant.employee.open_request(request)["status"] == "pending"


def test_申請者は承認される前なら自分で取り下げられる(tenant):
    expense = tenant.expense_template()
    request = tenant.employee.file_request(expense, "取り下げる精算", amount=3000, purpose="誤登録")

    # 他人は取り下げられない
    with pytest.raises(ApiError) as error:
        tenant.manager.cancel(request)
    assert error.value.status == 403

    assert tenant.employee.cancel(request)["status"] == "cancelled"
    assert tenant.manager.inbox() == []


def test_入力に不備がある申請は提出できない(tenant):
    expense = tenant.expense_template()

    with pytest.raises(ApiError) as error:
        tenant.employee.file_request(expense, "不備のある精算", amount="たくさん")

    assert error.value.status == 422
    assert set(error.value.errors) == {"amount", "purpose"}
    # 提出されていないので、上長の未処理箱は空のまま
    assert tenant.manager.inbox() == []
    # 現状の仕様: 提出は失敗するが、入力内容は下書きとして残る
    assert [item["title"] for item in tenant.employee.my_requests(status="draft")] == [
        "不備のある精算"
    ]


def test_申請にコメントを付けて承認者とやり取りできる(tenant):
    expense = tenant.expense_template()
    request = tenant.employee.file_request(
        expense, "備品購入の精算", amount=15000, purpose="開発用ケーブル一式"
    )

    tenant.manager.comment_on(request, "領収書の原本を経理部へ提出してください")
    tenant.employee.comment_on(request, "本日提出しました")

    thread = [comment["body"] for comment in tenant.employee.open_request(request)["comments"]]
    assert thread == ["領収書の原本を経理部へ提出してください", "本日提出しました"]

    # 申請に関与していない同僚はコメントできない
    with pytest.raises(ApiError) as error:
        tenant.colleague.comment_on(request, "私も見たい")
    assert error.value.status == 403
