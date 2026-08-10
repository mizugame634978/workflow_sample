"""シナリオテストの実行基盤。

単体テスト（``tests/conftest.py``）がテストごとに空のインメモリ DB を使うのに対し、
シナリオテストは **1つのデータベースをセッション全体で共有** する。
これは本番に近い状況であり、「テスト同士がデータで干渉しないこと」を
仕組みとして検証するためでもある。独立性は法人（テナント）の分離で担保する。
"""

from __future__ import annotations

import os
import re
from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker

from app.models import Base
from tests.scenarios.world import TenantFactory


@pytest.fixture(scope="session")
def scenario_engine(tmp_path_factory: pytest.TempPathFactory) -> Iterator[Engine]:
    """全シナリオが共有するデータベース。

    ``pytest-xdist`` で並列実行する場合はワーカーごとにファイルを分ける
    （SQLite は複数プロセスからの書き込みに向かないため）。
    どちらの場合も、1つの DB を複数のシナリオが共有する点は変わらない。
    """
    worker = os.environ.get("PYTEST_XDIST_WORKER", "main")
    database = tmp_path_factory.getbasetemp() / f"scenarios-{worker}.db"
    engine = create_engine(
        f"sqlite:///{database}", connect_args={"check_same_thread": False}, future=True
    )
    Base.metadata.create_all(engine)
    try:
        yield engine
    finally:
        engine.dispose()


@pytest.fixture(scope="session")
def scenario_sessions(scenario_engine: Engine) -> sessionmaker:
    return sessionmaker(bind=scenario_engine, autoflush=False, future=True)


@pytest.fixture()
def api(scenario_sessions: sessionmaker) -> Iterator[TestClient]:
    """本物のアプリ。リクエストごとに新しいセッションを渡す（本番と同じ経路）。"""
    from app.api.deps import get_db
    from app.main import app

    def request_scoped_session():
        session = scenario_sessions()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = request_scoped_session
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()


@pytest.fixture()
def tenants(api: TestClient, scenario_sessions: sessionmaker, request: pytest.FixtureRequest):
    """テスト法人のファクトリ。1シナリオで複数の法人を作ることもできる。"""
    return TenantFactory(scenario_sessions, api, label=_label(request.node.name))


@pytest.fixture()
def tenant(tenants: TenantFactory):
    """このシナリオ専用の法人。他のシナリオとはデータが完全に分離される。"""
    return tenants.create()


def _label(node_name: str) -> str:
    """テスト名を slug に使える形へ（失敗時にどの法人か追えるようにする）。"""
    ascii_only = re.sub(r"[^a-zA-Z0-9]+", "-", node_name).strip("-").lower()
    return (ascii_only or "scenario")[:24]
