"""ASGI application factory."""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.routers import api_router
from app.core.config import settings
from app.core.db import init_db
from app.services.errors import WorkflowError

logger = logging.getLogger("workflow")

DESCRIPTION = """
社内申請・承認ワークフロー SaaS のバックエンド API。

* マルチテナント（組織単位でデータを完全分離）
* 申請フォームと承認ルートをテンプレートとして定義
* 申請 → 承認 / 却下 / 差戻し / 取り下げ の状態遷移を一元管理
* すべての状態遷移を監査ログとして追記のみで記録
"""


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    init_db()
    logger.info("workflow api started (env=%s)", settings.environment)
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title=f"{settings.app_name} API",
        description=DESCRIPTION,
        version="1.0.0",
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(api_router)

    @app.get("/healthz", tags=["meta"], summary="ヘルスチェック")
    def healthz() -> dict[str, str]:
        return {"status": "ok", "app": settings.app_name, "environment": settings.environment}

    @app.exception_handler(WorkflowError)
    async def _workflow_error(_: Request, exc: WorkflowError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code, content={"message": exc.message, "errors": exc.errors}
        )

    @app.exception_handler(StarletteHTTPException)
    async def _http_error(_: Request, exc: StarletteHTTPException) -> JSONResponse:
        detail = exc.detail if isinstance(exc.detail, str) else "リクエストを処理できませんでした"
        return JSONResponse(
            status_code=exc.status_code,
            content={"message": detail, "errors": {}},
            headers=exc.headers,
        )

    @app.exception_handler(RequestValidationError)
    async def _validation_error(_: Request, exc: RequestValidationError) -> JSONResponse:
        errors = {
            ".".join(str(part) for part in error["loc"][1:]): error["msg"]
            for error in exc.errors()
        }
        return JSONResponse(
            status_code=422, content={"message": "入力内容を確認してください", "errors": errors}
        )

    return app


app = create_app()
