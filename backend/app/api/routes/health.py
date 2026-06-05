from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.orm import Session

from fastapi import APIRouter, Depends

from backend.app.core.config import settings
from backend.app.core.database import get_db
from backend.app.core.redis_client import get_redis
from backend.app.schemas.audit import HealthResponse


router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check(db: Session = Depends(get_db)) -> HealthResponse:
    database_status = "ok"
    redis_status = "ok"

    try:
        db.execute(text("SELECT 1"))
    except Exception:
        database_status = "error"

    try:
        redis = await get_redis()
        await redis.ping()
    except Exception:
        redis_status = "error"

    return HealthResponse(app=settings.app_name, database=database_status, redis=redis_status)

