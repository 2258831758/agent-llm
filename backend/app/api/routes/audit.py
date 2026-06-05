from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.models import AuditTask
from backend.app.schemas.audit import AuditTaskResponse, StartAuditRequest, StartAuditResponse
from backend.app.services.audit_service import schedule_audit, serialize_task
from backend.app.services.events import event_bus


router = APIRouter()


@router.post("/audit/start", response_model=StartAuditResponse)
async def start_audit(payload: StartAuditRequest, db: Session = Depends(get_db)) -> StartAuditResponse:
    task = db.get(AuditTask, payload.task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    if task.status == "running":
        raise HTTPException(status_code=409, detail="Task is already running")
    if not task.upload_path:
        raise HTTPException(status_code=400, detail="Task upload is missing")

    task.status = "queued"
    db.commit()
    schedule_audit(task.id)

    return StartAuditResponse(task_id=task.id, status="running")


@router.get("/audit/{task_id}", response_model=AuditTaskResponse)
def get_audit_result(task_id: str, db: Session = Depends(get_db)) -> AuditTaskResponse:
    task = db.get(AuditTask, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return AuditTaskResponse.model_validate(serialize_task(task))


@router.websocket("/ws/audit/{task_id}")
async def audit_stream(websocket: WebSocket, task_id: str) -> None:
    await websocket.accept()
    history = await event_bus.read_history(task_id)
    for item in history:
        await websocket.send_json(item)

    try:
        async for item in event_bus.subscribe(task_id):
            await websocket.send_json(item)
    except WebSocketDisconnect:
        return

