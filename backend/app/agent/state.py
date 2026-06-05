from __future__ import annotations

from typing import Any

from typing_extensions import TypedDict


class AuditFinding(TypedDict, total=False):
    source: str
    severity: str
    title: str
    description: str
    file_path: str
    line_number: int
    cvss_score: float
    metadata: dict[str, Any]


class AuditState(TypedDict):
    task_id: str
    user_id: str
    task_name: str
    file_path: str
    project_path: str
    language: str
    framework: str
    entrypoint: str
    sandbox_id: str
    scan_results: list[AuditFinding]
    llm_results: list[AuditFinding]
    findings: list[AuditFinding]
    report_paths: dict[str, str]
    status: str
    logs: list[str]

