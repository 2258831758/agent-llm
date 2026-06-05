from __future__ import annotations

from fastapi import APIRouter

from backend.app.api.routes import audit, health, report, sandbox, upload


api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(upload.router, tags=["upload"])
api_router.include_router(audit.router, tags=["audit"])
api_router.include_router(report.router, tags=["report"])
api_router.include_router(sandbox.router, tags=["sandbox"])

