"""Populate the local database with a realistic demo tenant.

    python -m app.seed          # create if missing
    python -m app.seed --reset  # drop everything first
"""

from __future__ import annotations

import argparse
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.db import SessionLocal, engine, init_db
from app.core.security import hash_password
from app.models import (
    ApproverType,
    Base,
    Organization,
    Request,
    RequestStatus,
    TemplateStep,
    User,
    UserRole,
    WorkflowTemplate,
)
from app.services import workflow_service as wf

DEMO_PASSWORD = "Password123!"

PEOPLE = [
    # key, email, name, department, job title, role, manager key
    ("ceo", "takahashi@acme.co.jp", "高橋 誠", "経営企画本部", "代表取締役", UserRole.MEMBER, None),
    ("director", "sato@acme.co.jp", "佐藤 直子", "開発本部", "本部長", UserRole.MEMBER, "ceo"),
    ("manager", "suzuki@acme.co.jp", "鈴木 健一", "プロダクト開発部", "課長", UserRole.MEMBER, "director"),
    ("employee", "tanaka@acme.co.jp", "田中 美咲", "プロダクト開発部", "主任", UserRole.MEMBER, "manager"),
    ("employee2", "yamamoto@acme.co.jp", "山本 拓也", "プロダクト開発部", "エンジニア", UserRole.MEMBER, "manager"),
    ("accounting", "nakamura@acme.co.jp", "中村 彩", "経理部", "経理担当", UserRole.ADMIN, "director"),
    ("admin", "admin@acme.co.jp", "管理 太郎", "情報システム部", "システム管理者", UserRole.ADMIN, "director"),
]

TEMPLATES = [
    {
        "code": "EXPENSE",
        "name": "経費精算申請",
        "category": "経理",
        "icon": "receipt",
        "description": "立替払いした経費の精算を申請します。領収書は原本を経理部へ提出してください。",
        "form_fields": [
            {"key": "expense_date", "label": "利用日", "type": "date", "required": True},
            {
                "key": "category",
                "label": "費目",
                "type": "select",
                "required": True,
                "options": ["交通費", "接待交際費", "消耗品費", "書籍・研修費"],
            },
            {"key": "amount", "label": "金額（円）", "type": "number", "required": True, "min": 1},
            {"key": "purpose", "label": "利用目的", "type": "textarea", "required": True},
            {"key": "receipt_no", "label": "領収書番号", "type": "text", "required": False},
        ],
        "steps": [
            ("上長承認", ApproverType.MANAGER, None, None),
            ("経理承認", ApproverType.ROLE, None, UserRole.ADMIN),
        ],
    },
    {
        "code": "LEAVE",
        "name": "休暇申請",
        "category": "人事",
        "icon": "calendar",
        "description": "有給休暇・特別休暇の取得を申請します。原則として3営業日前までに提出してください。",
        "form_fields": [
            {
                "key": "leave_type",
                "label": "休暇区分",
                "type": "select",
                "required": True,
                "options": ["有給休暇", "特別休暇", "慶弔休暇", "リフレッシュ休暇"],
            },
            {"key": "start_date", "label": "開始日", "type": "date", "required": True},
            {"key": "end_date", "label": "終了日", "type": "date", "required": True},
            {"key": "reason", "label": "理由", "type": "textarea", "required": False},
        ],
        "steps": [("上長承認", ApproverType.MANAGER, None, None)],
    },
    {
        "code": "PURCHASE",
        "name": "購買申請",
        "category": "総務",
        "icon": "cart",
        "description": "備品・ソフトウェアライセンス等の購入を申請します。10万円以上は部長承認が必要です。",
        "form_fields": [
            {"key": "item", "label": "品目", "type": "text", "required": True},
            {"key": "vendor", "label": "購入先", "type": "text", "required": True},
            {"key": "amount", "label": "金額（円）", "type": "number", "required": True, "min": 1},
            {"key": "need_by", "label": "希望納期", "type": "date", "required": False},
            {"key": "reason", "label": "必要理由", "type": "textarea", "required": True},
        ],
        "steps": [
            ("上長承認", ApproverType.MANAGER, None, None),
            ("本部長承認", ApproverType.USER, "director", None),
            ("経理承認", ApproverType.ROLE, None, UserRole.ADMIN),
        ],
    },
    {
        "code": "RINGI",
        "name": "稟議書",
        "category": "経営",
        "icon": "briefcase",
        "description": "新規施策・契約締結など、経営判断を要する事項の決裁を申請します。",
        "form_fields": [
            {"key": "amount", "label": "予算規模（円）", "type": "number", "required": True},
            {"key": "background", "label": "背景・課題", "type": "textarea", "required": True},
            {"key": "proposal", "label": "施策内容", "type": "textarea", "required": True},
            {"key": "effect", "label": "期待効果", "type": "textarea", "required": True},
        ],
        "steps": [
            ("課長承認", ApproverType.USER, "manager", None),
            ("本部長承認", ApproverType.USER, "director", None),
            ("最終決裁", ApproverType.USER, "ceo", None),
        ],
    },
    {
        "code": "TRIP",
        "name": "出張申請",
        "category": "総務",
        "icon": "plane",
        "description": "国内・海外出張の事前申請です。旅費の精算は別途経費精算申請を提出してください。",
        "form_fields": [
            {"key": "destination", "label": "出張先", "type": "text", "required": True},
            {"key": "start_date", "label": "出発日", "type": "date", "required": True},
            {"key": "end_date", "label": "帰着日", "type": "date", "required": True},
            {"key": "estimated_cost", "label": "概算費用（円）", "type": "number", "required": True},
            {"key": "purpose", "label": "目的", "type": "textarea", "required": True},
        ],
        "steps": [
            ("上長承認", ApproverType.MANAGER, None, None),
            ("経理承認", ApproverType.ROLE, None, UserRole.ADMIN),
        ],
    },
]


def seed(reset: bool = False) -> None:
    if reset:
        Base.metadata.drop_all(engine)
    init_db()

    with SessionLocal() as db:
        if db.scalars(select(Organization).limit(1)).first() is not None:
            print("既にデータが存在するためスキップしました（--reset で作り直せます）")
            return

        org = Organization(name="アクメ株式会社", slug="acme")
        db.add(org)
        db.flush()

        people: dict[str, User] = {}
        for key, email, name, department, title, role, manager_key in PEOPLE:
            user = User(
                organization_id=org.id,
                email=email,
                name=name,
                department=department,
                job_title=title,
                role=role,
                password_hash=hash_password(DEMO_PASSWORD),
                manager_id=people[manager_key].id if manager_key else None,
            )
            db.add(user)
            db.flush()
            people[key] = user

        templates: dict[str, WorkflowTemplate] = {}
        for spec in TEMPLATES:
            template = WorkflowTemplate(
                organization_id=org.id,
                code=spec["code"],
                name=spec["name"],
                description=spec["description"],
                category=spec["category"],
                icon=spec["icon"],
                form_fields=spec["form_fields"],
                created_by_id=people["admin"].id,
            )
            for index, (step_name, approver_type, user_key, role) in enumerate(spec["steps"]):
                template.steps.append(
                    TemplateStep(
                        order_index=index,
                        name=step_name,
                        approver_type=approver_type,
                        approver_user_id=people[user_key].id if user_key else None,
                        approver_role=role,
                    )
                )
            db.add(template)
            db.flush()
            templates[spec["code"]] = template

        db.commit()
        _seed_requests(db, people, templates)
        print(f"デモデータを作成しました: {len(people)} ユーザー / {len(templates)} フォーム")
        print(f"ログイン例: {PEOPLE[3][1]} / {DEMO_PASSWORD}")


def _seed_requests(db: Session, people: dict[str, User], templates: dict) -> None:
    now = datetime.now(UTC)
    tanaka, yamamoto = people["employee"], people["employee2"]
    suzuki, nakamura = people["manager"], people["accounting"]

    # 1. 完全に承認された経費精算（先月）
    approved = _make(
        db,
        tanaka,
        templates["EXPENSE"],
        "10月度 交通費精算",
        {
            "expense_date": _day(now, -38),
            "category": "交通費",
            "amount": 12480,
            "purpose": "顧客訪問（大阪）に伴う新幹線往復運賃",
            "receipt_no": "R-20251015-004",
        },
    )
    wf.approve(db, actor=suzuki, request=approved, comment="確認しました")
    wf.approve(db, actor=nakamura, request=approved, comment="経理処理済みです")
    _backdate(db, approved, created=now - timedelta(days=38), completed=now - timedelta(days=36))

    # 2. 承認待ち（課長のインボックスに入る）
    pending = _make(
        db,
        tanaka,
        templates["PURCHASE"],
        "開発用モニター（27インチ）3台の購入",
        {
            "item": "27インチ 4K モニター ×3",
            "vendor": "株式会社サンプル電機",
            "amount": 178000,
            "need_by": _day(now, 14),
            "reason": "新規参画メンバー3名分の開発環境整備のため。既存在庫はありません。",
        },
    )
    _backdate(db, pending, created=now - timedelta(days=2))
    wf.add_comment(
        db, actor=tanaka, request=pending, body="見積書は共有ドライブの /purchase/2026 に格納しています。"
    )

    # 3. 稟議（本部長承認待ち）
    ringi = _make(
        db,
        suzuki,
        templates["RINGI"],
        "顧客サポート基盤の刷新（SaaS 導入）",
        {
            "amount": 4800000,
            "background": "問い合わせ件数が前年比 180% となり、現行のメール運用では初回応答 24 時間を超過している。",
            "proposal": "SaaS 型カスタマーサポート基盤を導入し、チャネル統合とテンプレート応答を整備する。",
            "effect": "初回応答時間を 4 時間以内に短縮し、サポート担当の工数を月 120 時間削減する。",
        },
    )
    _backdate(db, ringi, created=now - timedelta(days=5))

    # 4. 差戻し（下書きに戻っている）
    sent_back = _make(
        db,
        yamamoto,
        templates["EXPENSE"],
        "書籍購入費の精算",
        {
            "expense_date": _day(now, -6),
            "category": "書籍・研修費",
            "amount": 8600,
            "purpose": "設計スキル向上のための技術書購入",
        },
    )
    wf.send_back(
        db,
        actor=suzuki,
        request=sent_back,
        comment="購入した書籍のタイトルを利用目的に追記してください。",
    )
    _backdate(db, sent_back, created=now - timedelta(days=6))

    # 5. 却下
    rejected = _make(
        db,
        yamamoto,
        templates["TRIP"],
        "海外カンファレンス参加（サンフランシスコ）",
        {
            "destination": "アメリカ・サンフランシスコ",
            "start_date": _day(now, 30),
            "end_date": _day(now, 35),
            "estimated_cost": 620000,
            "purpose": "技術カンファレンス参加による最新動向の調査",
        },
    )
    wf.reject(
        db,
        actor=suzuki,
        request=rejected,
        comment="今期の出張予算を超過するため、オンライン参加への切り替えを検討してください。",
    )
    _backdate(db, rejected, created=now - timedelta(days=20), completed=now - timedelta(days=19))

    # 6. 下書き
    draft = wf.create_draft(
        db,
        actor=tanaka,
        template=templates["LEAVE"],
        title="有給休暇の取得（帰省）",
        form_data={"leave_type": "有給休暇", "start_date": _day(now, 21), "end_date": _day(now, 23)},
    )
    _backdate(db, draft, created=now - timedelta(days=1))

    # 7-9. 過去の承認済み案件（グラフに厚みを持たせる）
    history = [
        (
            yamamoto,
            "LEAVE",
            "有給休暇の取得",
            65,
            {
                "leave_type": "有給休暇",
                "start_date": _day(now, -60),
                "end_date": _day(now, -60),
            },
        ),
        (
            tanaka,
            "EXPENSE",
            "9月度 交際費精算",
            72,
            {
                "expense_date": _day(now, -75),
                "category": "接待交際費",
                "amount": 34500,
                "purpose": "取引先との定例会食",
            },
        ),
        (
            suzuki,
            "PURCHASE",
            "チーム用ホワイトボードの購入",
            100,
            {
                "item": "電子ホワイトボード",
                "vendor": "オフィス総研株式会社",
                "amount": 96000,
                "reason": "設計レビューの効率化のため",
            },
        ),
    ]
    for applicant, code, title, days_ago, form in history:
        record = _make(db, applicant, templates[code], title, form)
        while record.status is RequestStatus.PENDING:
            step = record.current_step
            approver = _resolve_actor(db, record, step)
            wf.approve(db, actor=approver, request=record, comment="承認します")
        _backdate(
            db,
            record,
            created=now - timedelta(days=days_ago),
            completed=now - timedelta(days=days_ago - 1),
        )

    # 承認待ちを経理（管理者）のインボックスにも積む
    awaiting_finance = _make(
        db,
        yamamoto,
        templates["TRIP"],
        "名古屋支社での合同開発合宿",
        {
            "destination": "愛知県名古屋市",
            "start_date": _day(now, 10),
            "end_date": _day(now, 12),
            "estimated_cost": 78000,
            "purpose": "支社メンバーとの合同開発合宿への参加",
        },
    )
    wf.approve(db, actor=suzuki, request=awaiting_finance, comment="問題ありません")
    _backdate(db, awaiting_finance, created=now - timedelta(days=3))


def _make(db: Session, applicant: User, template, title: str, form: dict) -> Request:
    request = wf.create_draft(
        db, actor=applicant, template=template, title=title, form_data=form
    )
    return wf.submit(db, actor=applicant, request=request)


def _resolve_actor(db: Session, request: Request, step) -> User:
    if step.approver_id is not None:
        return db.get(User, step.approver_id)
    return db.scalars(
        select(User).where(
            User.organization_id == request.organization_id,
            User.role == step.approver_role,
            User.id != request.applicant_id,
        )
    ).first()


def _backdate(
    db: Session,
    request: Request,
    *,
    created: datetime,
    completed: datetime | None = None,
) -> None:
    request.created_at = created
    request.updated_at = completed or created
    if request.submitted_at is not None:
        request.submitted_at = created
    if completed is not None and request.completed_at is not None:
        request.completed_at = completed
    db.commit()


def _day(now: datetime, offset: int) -> str:
    return (now + timedelta(days=offset)).date().isoformat()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="デモデータを投入します")
    parser.add_argument("--reset", action="store_true", help="既存データを削除してから投入する")
    seed(reset=parser.parse_args().reset)
