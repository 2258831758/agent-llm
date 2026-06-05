from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from sqlalchemy.orm import Session

from backend.app.agent.graph import build_audit_graph
from backend.app.core.database import SessionLocal
from backend.app.models import AuditTask, Finding, User
from backend.app.services.events import event_bus

_background_tasks: set[asyncio.Task[None]] = set()


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def ensure_user(db: Session, user_id: str) -> User:
    user = db.get(User, user_id)
    if user is None:
        user = User(
            id=user_id,
            username="local-demo",
            email="local-demo@example.com",
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    return user


def serialize_task(task: AuditTask) -> dict[str, object]:
    return {
        "id": task.id,
        "user_id": task.user_id,
        "task_name": task.task_name,
        "status": task.status,
        "language": task.language,
        "framework": task.framework,
        "upload_name": task.upload_name,
        "project_path": task.project_path,
        "report_dir": task.report_dir,
        "created_at": task.created_at,
        "started_at": task.started_at,
        "finished_at": task.finished_at,
        "findings": [item.as_dict() for item in task.findings],
    }


async def run_audit_task(task_id: str) -> None:
    db = SessionLocal()
    try:
        task = db.get(AuditTask, task_id)
        if task is None:
            return

        task.status = "running"
        task.started_at = utcnow()
        db.commit()

        await event_bus.publish(task_id, {"event": "progress", "value": 5, "message": "审计任务已入队"})

        graph = build_audit_graph()
        initial_state = {
            "task_id": task.id,
            "user_id": task.user_id,
            "task_name": task.task_name,
            "file_path": task.upload_path or "",
            "project_path": task.project_path or "",
            "language": task.language or "",
            "framework": task.framework or "",
            "entrypoint": "",
            "sandbox_id": "",
            "scan_results": [],
            "llm_results": [],
            "findings": [],
            "report_paths": {},
            "status": "running",
            "logs": [],
        }

        result = await graph.ainvoke(initial_state)

        task.language = result["language"] or None
        task.framework = result["framework"] or None
        task.project_path = result["project_path"] or None
        task.report_dir = result["report_paths"].get("report_dir")
        task.status = "completed"
        task.finished_at = utcnow()

        db.query(Finding).filter(Finding.task_id == task.id).delete()
        for item in result["findings"]:
            db.add(
                Finding(
                    id=str(uuid4()),
                    task_id=task.id,
                    source=str(item["source"]),
                    severity=str(item["severity"]),
                    title=str(item["title"]),
                    description=str(item["description"]),
                    file_path=str(item["file_path"]),
                    line_number=int(item["line_number"]),
                    cvss_score=float(item["cvss_score"]),
                )
            )
        db.commit()

        await event_bus.publish(
            task_id,
            {
                "event": "progress",
                "value": 100,
                "message": f"审计完成，共发现 {len(result['findings'])} 条漏洞",
            },
        )
    except Exception as exc:
        task = db.get(AuditTask, task_id)
        if task is not None:
            task.status = "failed"
            task.finished_at = utcnow()
            db.commit()
        await event_bus.publish(task_id, {"event": "log", "message": f"审计失败：{exc}"})
    finally:
        db.close()


def schedule_audit(task_id: str) -> asyncio.Task[None]:
    task = asyncio.create_task(run_audit_task(task_id))
    _background_tasks.add(task)
    task.add_done_callback(_background_tasks.discard)
    return task


def report_paths(task: AuditTask) -> dict[str, Path]:
    if not task.report_dir:
        return {}
    report_dir = Path(task.report_dir)
    return {
        "report_dir": report_dir,
        "markdown": report_dir / "report.md",
        "html": report_dir / "report.html",
        "json": report_dir / "report.json",
    }
