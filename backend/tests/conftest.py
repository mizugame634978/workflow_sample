"""Shared pytest fixtures.

Every test runs against a throw-away in-memory SQLite database so the suite is
hermetic and can be executed in parallel without shared state.
"""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import settings

# Keep the suite fast: production-grade KDF cost is verified in test_security.py.
settings.password_hash_iterations = 1_000
# Never touch the developer's local database file from the test suite.
settings.database_url = "sqlite://"

from app.core.security import hash_password  # noqa: E402
from app.models import (
    Base,
    Organization,
    TemplateStep,
    User,
    UserRole,
    WorkflowTemplate,
)


@pytest.fixture()
def db() -> Iterator[Session]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        future=True,
    )
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, autoflush=False, future=True)
    session = factory()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


@pytest.fixture()
def org(db: Session) -> Organization:
    organization = Organization(name="Acme Corporation", slug="acme")
    db.add(organization)
    db.commit()
    db.refresh(organization)
    return organization


def make_user(
    db: Session,
    org: Organization,
    *,
    email: str,
    name: str = "Test User",
    role: UserRole = UserRole.MEMBER,
    department: str = "Engineering",
    manager: User | None = None,
) -> User:
    user = User(
        organization_id=org.id,
        email=email,
        name=name,
        role=role,
        department=department,
        password_hash=hash_password("Password123!"),
        manager_id=manager.id if manager else None,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def make_template(
    db: Session,
    org: Organization,
    creator: User,
    *,
    code: str = "EXPENSE",
    name: str = "経費精算申請",
    form_fields: list[dict] | None = None,
    steps: list[dict] | None = None,
) -> WorkflowTemplate:
    template = WorkflowTemplate(
        organization_id=org.id,
        code=code,
        name=name,
        description="経費の精算を申請します。",
        category="経理",
        created_by_id=creator.id,
        form_fields=form_fields
        if form_fields is not None
        else [
            {"key": "amount", "label": "金額", "type": "number", "required": True},
            {"key": "purpose", "label": "利用目的", "type": "textarea", "required": True},
        ],
    )
    db.add(template)
    db.flush()
    for index, step in enumerate(steps or [{"name": "上長承認", "approver_type": "manager"}]):
        db.add(
            TemplateStep(
                template_id=template.id,
                order_index=index,
                name=step["name"],
                approver_type=step["approver_type"],
                approver_user_id=step.get("approver_user_id"),
                approver_role=step.get("approver_role"),
            )
        )
    db.commit()
    db.refresh(template)
    return template


@pytest.fixture()
def client(db: Session) -> Iterator[TestClient]:
    from app.api.deps import get_db
    from app.main import app

    app.dependency_overrides[get_db] = lambda: db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def login(client: TestClient, email: str, password: str = "Password123!") -> dict[str, str]:
    """Log in and return an ``Authorization`` header ready to be passed to httpx."""
    response = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200, response.text
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


@pytest.fixture()
def users(db: Session, org: Organization) -> dict[str, User]:
    admin = make_user(
        db, org, email="admin@acme.co.jp", name="管理 太郎", role=UserRole.ADMIN, department="情報システム"
    )
    director = make_user(db, org, email="director@acme.co.jp", name="部長 花子", department="経営企画")
    manager = make_user(
        db, org, email="manager@acme.co.jp", name="課長 次郎", department="Engineering", manager=director
    )
    employee = make_user(
        db, org, email="employee@acme.co.jp", name="社員 三郎", department="Engineering", manager=manager
    )
    return {"admin": admin, "director": director, "manager": manager, "employee": employee}
