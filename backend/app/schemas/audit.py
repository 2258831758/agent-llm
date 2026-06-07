from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class UploadResponse(BaseModel):
    task_id: str
    status: str
    upload_name: str
    upload_count: int = 1
    upload_names: list[str] = Field(default_factory=list)


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
    owasp_id: str | None = None
    owasp_name: str | None = None
    owasp_label: str | None = None
    cwe_id: str | None = None
    impact: str | None = None
    recommendation: str | None = None
    reproduction_steps: list[str] = Field(default_factory=list)
    evidence: str | None = None
    code_snippet: str | None = None
    related_files: list[str] = Field(default_factory=list)
    related_cves: list[str] = Field(default_factory=list)
    ctf_scenarios: list[str] = Field(default_factory=list)
    references: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


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
