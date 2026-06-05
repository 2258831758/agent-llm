from __future__ import annotations

from fastapi import APIRouter, Query

from backend.app.schemas.audit import SandboxCreateResponse
from backend.app.services.sandbox import get_sandbox_runner


router = APIRouter()


@router.post("/sandbox/session", response_model=SandboxCreateResponse)
async def create_sandbox_session(task_id: str = Query(..., description="Audit task id")) -> SandboxCreateResponse:
    session = await get_sandbox_runner().create(task_id)
    return SandboxCreateResponse(
        sandbox_id=session.sandbox_id,
        status=session.status,
        message=session.message,
    )

