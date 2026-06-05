from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class UploadResponse(BaseModel):
    task_id: str
    status: str
    upload_name: str


class StartAuditRequest(BaseModel):
    task_id: str


class StartAuditResponse(BaseModel):
    task_id: str
    status: str


class FindingResponse(BaseModel):
    id: str
    source: str
    severity: str
    title: str
    description: str
    file_path: str
    line_number: int
    cvss_score: float


class AuditTaskResponse(BaseModel):
    id: str
    user_id: str
    task_name: str
    status: str
    language: str | None = None
    framework: str | None = None
    upload_name: str | None = None
    project_path: str | None = None
    report_dir: str | None = None
    created_at: datetime
    started_at: datetime | None = None
    finished_at: datetime | None = None
    findings: list[FindingResponse] = Field(default_factory=list)


class EventPayload(BaseModel):
    event: str
    message: str | None = None
    agent: str | None = None
    status: str | None = None
    value: int | None = None
    data: dict[str, Any] | None = None
    created_at: datetime | None = None


class HealthResponse(BaseModel):
    app: str
    database: str
    redis: str


class SandboxCreateResponse(BaseModel):
    sandbox_id: str
    status: str
    message: str

