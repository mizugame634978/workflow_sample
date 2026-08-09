"""API v1 routers."""

from fastapi import APIRouter

from app.api.routers import analytics, auth, notifications, requests, templates, users

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(templates.router)
api_router.include_router(requests.router)
api_router.include_router(notifications.router)
api_router.include_router(analytics.router)

__all__ = ["api_router"]
