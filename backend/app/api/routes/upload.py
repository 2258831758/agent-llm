from __future__ import annotations

from uuid import uuid4

from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.core.database import get_db
from backend.app.models import AuditTask
from backend.app.schemas.audit import UploadResponse
from backend.app.services.audit_service import ensure_user
from backend.app.services.files import build_demo_upload, save_upload


router = APIRouter()


def _create_task_record(
    *,
    task_id: str,
    user_id: str,
    task_name: str,
    upload_name: str,
    upload_path: str,
    db: Session,
) -> UploadResponse:
    task = AuditTask(
        id=task_id,
        user_id=user_id,
        task_name=task_name,
        status="uploaded",
        upload_name=upload_name,
        upload_path=upload_path,
    )
    db.add(task)
    db.commit()
    return UploadResponse(task_id=task_id, status=task.status, upload_name=upload_name)


@router.post("/upload", response_model=UploadResponse)
async def upload_source_code(
    file: UploadFile = File(...),
    task_name: str | None = Form(default=None),
    user_id: str | None = Form(default=None),
    db: Session = Depends(get_db),
) -> UploadResponse:
    task_id = str(uuid4())
    effective_user_id = user_id or settings.default_user_id
    ensure_user(db, effective_user_id)
    upload_path = await save_upload(task_id, file)

    return _create_task_record(
        task_id=task_id,
        user_id=effective_user_id,
        task_name=task_name or upload_path.stem,
        upload_name=upload_path.name,
        upload_path=str(upload_path),
        db=db,
    )


@router.post("/upload/demo", response_model=UploadResponse)
async def upload_demo_project(
    task_name: str | None = Form(default=None),
    user_id: str | None = Form(default=None),
    db: Session = Depends(get_db),
) -> UploadResponse:
    task_id = str(uuid4())
    effective_user_id = user_id or settings.default_user_id
    ensure_user(db, effective_user_id)
    upload_path = build_demo_upload(task_id)

    return _create_task_record(
        task_id=task_id,
        user_id=effective_user_id,
        task_name=task_name or "vulnerable_python_app",
        upload_name=upload_path.name,
        upload_path=str(upload_path),
        db=db,
    )
