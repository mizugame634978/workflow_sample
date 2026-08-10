"""シナリオテスト用のドメイン言語（DSL）。

シナリオテストは「誰が何をしたら、どうなるか」を業務の言葉で記述する。
そのため HTTP の詳細（パス・ステータスコード・トークン）はここに閉じ込め、
テスト本体には ``manager.approve(request)`` のような操作だけが並ぶようにする。

テスト間の独立性は **法人（テナント）単位** で担保する。
``TenantFactory.create()`` は毎回ユニークな法人・ユーザー・メールアドレスを
払い出すため、同じデータベースを共有していてもシナリオ同士は干渉しない。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, sessionmaker

from app.core.security import hash_password
from app.models import Organization, User, UserRole

API = "/api/v1"
PASSWORD = "Scenario123!"


class ApiError(Exception):
    """API が業務エラーを返したことを表す。シナリオ側では status で分岐する。"""

    def __init__(self, status: int, method: str, path: str, payload: dict[str, Any]) -> None:
        self.status = status
        self.method = method
        self.path = path
        self.message = payload.get("message", "")
        self.errors: dict[str, str] = payload.get("errors", {}) or {}
        super().__init__(f"{method} {path} -> {status}: {self.message} {self.errors}")


@dataclass
class Actor:
    """法人に所属する1人の利用者。API 越しに業務操作を行う。"""

    key: str
    id: int
    name: str
    email: str
    department: str
    role: UserRole
    api: TestClient
    _token: str | None = field(default=None, repr=False)

    # ------------------------------------------------------------------ 認証

    @property
    def headers(self) -> dict[str, str]:
        if self._token is None:
            body = self._request(
                "POST", f"{API}/auth/login", json={"email": self.email, "password": PASSWORD}
            )
            self._token = body["access_token"]
        return {"Authorization": f"Bearer {self._token}"}

    def profile(self) -> dict[str, Any]:
        return self._call("GET", f"{API}/auth/me")

    # ------------------------------------------------------------------ 申請

    def draft_request(self, template: dict, title: str, **form: Any) -> dict[str, Any]:
        """下書きとして申請を作成する。"""
        return self._create_request(template, title, form, submit=False)

    def file_request(self, template: dict, title: str, **form: Any) -> dict[str, Any]:
        """申請を作成してそのまま提出する。"""
        return self._create_request(template, title, form, submit=True)

    def update_draft(self, request: dict, title: str | None = None, **form: Any) -> dict[str, Any]:
        payload: dict[str, Any] = {}
        if title is not None:
            payload["title"] = title
        if form:
            payload["form_data"] = {**request["form_data"], **form}
        return self._call("PATCH", f"{API}/requests/{request['id']}", json=payload)

    def submit(self, request: dict) -> dict[str, Any]:
        return self._call("POST", f"{API}/requests/{request['id']}/submit")

    def cancel(self, request: dict) -> dict[str, Any]:
        return self._call("POST", f"{API}/requests/{request['id']}/cancel")

    # ------------------------------------------------------------------ 承認

    def approve(self, request: dict, comment: str = "") -> dict[str, Any]:
        return self._call(
            "POST", f"{API}/requests/{request['id']}/approve", json={"comment": comment}
        )

    def reject(self, request: dict, comment: str) -> dict[str, Any]:
        return self._call(
            "POST", f"{API}/requests/{request['id']}/reject", json={"comment": comment}
        )

    def send_back(self, request: dict, comment: str) -> dict[str, Any]:
        return self._call(
            "POST", f"{API}/requests/{request['id']}/send-back", json={"comment": comment}
        )

    def comment_on(self, request: dict, body: str) -> dict[str, Any]:
        return self._call(
            "POST", f"{API}/requests/{request['id']}/comments", json={"body": body}
        )

    # ------------------------------------------------------------------ 参照

    def open_request(self, request: dict | int) -> dict[str, Any]:
        request_id = request if isinstance(request, int) else request["id"]
        return self._call("GET", f"{API}/requests/{request_id}")

    def inbox(self) -> list[dict[str, Any]]:
        """自分の決裁を待っている申請。"""
        return self._call("GET", f"{API}/requests?scope=inbox&per_page=100")["items"]

    def my_requests(self, **params: Any) -> list[dict[str, Any]]:
        query = "&".join(f"{key}={value}" for key, value in params.items())
        suffix = f"&{query}" if query else ""
        return self._call("GET", f"{API}/requests?scope=mine&per_page=100{suffix}")["items"]

    def all_requests(self) -> list[dict[str, Any]]:
        """管理者のみ利用できる、法人全体の申請一覧。"""
        return self._call("GET", f"{API}/requests?scope=all&per_page=100")["items"]

    def available_templates(self) -> list[dict[str, Any]]:
        return self._call("GET", f"{API}/templates")["items"]

    def notifications(self) -> dict[str, Any]:
        return self._call("GET", f"{API}/notifications?limit=100")

    def dashboard(self) -> dict[str, Any]:
        return self._call("GET", f"{API}/analytics/summary")

    def colleagues(self) -> list[dict[str, Any]]:
        return self._call("GET", f"{API}/users")["items"]

    # ------------------------------------------------------------------ 管理操作

    def register_user(
        self,
        *,
        name: str,
        email: str,
        department: str = "",
        role: UserRole = UserRole.MEMBER,
        manager_id: int | None = None,
    ) -> dict[str, Any]:
        return self._call(
            "POST",
            f"{API}/users",
            json={
                "name": name,
                "email": email,
                "password": PASSWORD,
                "department": department,
                "role": role.value,
                "manager_id": manager_id,
            },
        )

    def revise_template(self, template: dict, **changes: Any) -> dict[str, Any]:
        return self._call("PATCH", f"{API}/templates/{template['id']}", json=changes)

    # ------------------------------------------------------------------ 内部

    def _create_request(
        self, template: dict, title: str, form: dict[str, Any], *, submit: bool
    ) -> dict[str, Any]:
        return self._call(
            "POST",
            f"{API}/requests",
            json={
                "template_id": template["id"],
                "title": title,
                "form_data": form,
                "submit": submit,
            },
        )

    def _call(self, method: str, path: str, json: Any = None) -> Any:
        return self._request(method, path, json=json, headers=self.headers)

    def _request(
        self, method: str, path: str, json: Any = None, headers: dict[str, str] | None = None
    ) -> Any:
        response = self.api.request(method, path, json=json, headers=headers)
        if response.status_code >= 400:
            body = response.json() if response.content else {}
            raise ApiError(response.status_code, method, path, body)
        if response.status_code == 204 or not response.content:
            return None
        return response.json()


class Tenant:
    """1つのテスト法人。所属ユーザーと申請フォームを保持する。"""

    def __init__(
        self,
        organization_id: int,
        name: str,
        slug: str,
        actors: dict[str, Actor],
        api: TestClient,
    ):
        self.id = organization_id
        self.name = name
        self.slug = slug
        self._actors = actors
        self._api = api

    def __getattr__(self, key: str) -> Actor:
        """``tenant.manager`` のように担当者へアクセスできるようにする。"""
        if key.startswith("_"):  # 内部属性は通常の解決に任せる（再帰防止）
            raise AttributeError(key)
        try:
            return self._actors[key]
        except KeyError as exc:  # pragma: no cover - テストの書き間違い検出用
            raise AttributeError(f"{self.name} に '{key}' はいません") from exc

    @property
    def people(self) -> dict[str, Actor]:
        return dict(self._actors)

    def email_for(self, local_part: str) -> str:
        """この法人だけで使われるメールアドレスを払い出す。"""
        return f"{local_part}@{self.slug}.co.jp"

    def hire(
        self,
        *,
        key: str,
        name: str,
        department: str = "",
        role: UserRole = UserRole.MEMBER,
        manager: Actor | None = None,
        by: Actor | None = None,
    ) -> Actor:
        """管理者として社員を登録し、その社員を登場人物として使えるようにする。"""
        recruiter = by or self.admin
        email = self.email_for(key)
        created = recruiter.register_user(
            name=name,
            email=email,
            department=department,
            role=role,
            manager_id=manager.id if manager else None,
        )
        actor = Actor(
            key=key,
            id=created["id"],
            name=name,
            email=email,
            department=department,
            role=role,
            api=self._api,
        )
        self._actors[key] = actor
        return actor

    # ------------------------------------------------------------------ フォーム

    def create_template(
        self,
        *,
        code: str,
        name: str,
        fields: list[dict[str, Any]],
        steps: list[dict[str, Any]],
        category: str = "共通",
        description: str = "",
    ) -> dict[str, Any]:
        """管理者としてフォームを定義する（API 経由）。"""
        return self.admin._call(
            "POST",
            f"{API}/templates",
            json={
                "code": code,
                "name": name,
                "description": description,
                "category": category,
                "form_fields": fields,
                "steps": steps,
            },
        )

    def expense_template(self) -> dict[str, Any]:
        """経費精算: 上長承認 → 経理（管理者権限）承認。"""
        return self.create_template(
            code="EXPENSE",
            name="経費精算申請",
            category="経理",
            description="立替経費の精算",
            fields=[
                {"key": "amount", "label": "金額（円）", "type": "number", "required": True, "min": 1},
                {"key": "purpose", "label": "利用目的", "type": "textarea", "required": True},
            ],
            steps=[
                {"name": "上長承認", "approver_type": "manager"},
                {"name": "経理承認", "approver_type": "role", "approver_role": "admin"},
            ],
        )

    def ringi_template(self) -> dict[str, Any]:
        """稟議: 課長 → 本部長 → 代表 の3段階決裁。"""
        return self.create_template(
            code="RINGI",
            name="稟議書",
            category="経営",
            description="経営判断を要する事項の決裁",
            fields=[
                {"key": "amount", "label": "予算規模（円）", "type": "number", "required": True},
                {"key": "proposal", "label": "施策内容", "type": "textarea", "required": True},
            ],
            steps=[
                {"name": "課長承認", "approver_type": "user", "approver_user_id": self.manager.id},
                {"name": "本部長承認", "approver_type": "user", "approver_user_id": self.director.id},
                {"name": "最終決裁", "approver_type": "user", "approver_user_id": self.ceo.id},
            ],
        )

    def leave_template(self) -> dict[str, Any]:
        """休暇申請: 上長承認のみの1段階。"""
        return self.create_template(
            code="LEAVE",
            name="休暇申請",
            category="人事",
            fields=[
                {"key": "start_date", "label": "開始日", "type": "date", "required": True},
                {"key": "reason", "label": "理由", "type": "text", "required": False},
            ],
            steps=[{"name": "上長承認", "approver_type": "manager"}],
        )


class TenantFactory:
    """テスト法人を払い出す。呼ぶたびに完全に独立した法人ができる。"""

    #: 役職キー -> (氏名, 部署, 役職名, 権限, 上長のキー)
    CAST: list[tuple[str, str, str, str, UserRole, str | None]] = [
        ("ceo", "高橋 誠", "経営企画本部", "代表取締役", UserRole.MEMBER, None),
        ("director", "佐藤 直子", "開発本部", "本部長", UserRole.MEMBER, "ceo"),
        ("manager", "鈴木 健一", "プロダクト開発部", "課長", UserRole.MEMBER, "director"),
        ("employee", "田中 美咲", "プロダクト開発部", "主任", UserRole.MEMBER, "manager"),
        ("colleague", "山本 拓也", "プロダクト開発部", "エンジニア", UserRole.MEMBER, "manager"),
        ("finance", "中村 彩", "経理部", "経理担当", UserRole.ADMIN, "director"),
        ("auditor", "小林 亮", "経理部", "経理監査", UserRole.ADMIN, "director"),
        ("admin", "管理 太郎", "情報システム部", "システム管理者", UserRole.ADMIN, "director"),
    ]

    def __init__(self, session_factory: sessionmaker, api: TestClient, label: str) -> None:
        self._session_factory = session_factory
        self._api = api
        self._label = label
        self._created: list[Tenant] = []

    def create(self, name_hint: str = "テスト商事") -> Tenant:
        slug = f"{self._label}-{uuid4().hex[:8]}"
        with self._session_factory() as session:
            tenant = self._provision(session, name_hint, slug)
        self._created.append(tenant)
        return tenant

    def _provision(self, session: Session, name_hint: str, slug: str) -> Tenant:
        organization = Organization(name=f"{name_hint}（{slug}）", slug=slug)
        session.add(organization)
        session.flush()

        password_hash = hash_password(PASSWORD)
        actors: dict[str, Actor] = {}
        records: dict[str, User] = {}

        for key, name, department, title, role, manager_key in self.CAST:
            user = User(
                organization_id=organization.id,
                # 法人ごとにドメインを変えるため、他のシナリオとメールが衝突しない
                email=f"{key}@{slug}.co.jp",
                name=name,
                department=department,
                job_title=title,
                role=role,
                password_hash=password_hash,
                manager_id=records[manager_key].id if manager_key else None,
            )
            session.add(user)
            session.flush()
            records[key] = user
            actors[key] = Actor(
                key=key,
                id=user.id,
                name=name,
                email=user.email,
                department=department,
                role=role,
                api=self._api,
            )

        session.commit()
        return Tenant(organization.id, organization.name, slug, actors, self._api)
