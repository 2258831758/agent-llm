from __future__ import annotations

from pydantic import BaseModel


class ReportSummaryResponse(BaseModel):
    task_id: str
    available_formats: list[str]
    report_dir: str
    markdown_path: str | None = None
    html_path: str | None = None
    json_path: str | None = None

